import time
import pandas as pd
import os
import shutil
import pickle

from ganon.config import Config
from ganon.util import check_file
from ganon.util import check_folder
from ganon.util import print_log
from ganon.util import run
from ganon.util import validate_input_files
from ganon.util import rm_files
from ganon.util import save_state
from ganon.util import set_output_folder
from ganon.util import load_state
from ganon.tax_util import get_file_info
from ganon.tax_util import get_sequence_info
from ganon.tax_util import parse_sequence_accession
from ganon.tax_util import parse_file_accession

from multitax import NcbiTx, GtdbTx


def build(cfg):
    files_output_folder = set_output_folder(cfg.db_prefix)
    if cfg.restart:
        restart_build(files_output_folder)

    assembly_summary = files_output_folder + "assembly_summary.txt"

    # Skip if already finished download from previous run
    if load_state("build_download", files_output_folder) and check_file(assembly_summary):
        print_log("Download finished - skipping", cfg.quiet)
    else:
        # If assembly_summary.txt was written and some files were already downloaded, try to fix
        resume_download = False
        if check_file(assembly_summary):
            if check_folder(files_output_folder + get_gu_current_version(assembly_summary) + "/files/"):
                print_log("Incomplete files detected, resuming download\n", cfg.quiet)
                resume_download = True

        tx = time.time()
        print_log("Downloading files from " + ",".join(cfg.source) + " [" + ",".join(cfg.organism_group) + "]", cfg.quiet)
        run_genome_updater_cmd = " ".join([cfg.path_exec['genome_updater'],
                                           "-d '" + ",".join(cfg.source) + "'",
                                           "-g '" + ",".join(cfg.organism_group) + "'",
                                           "-A " + str(cfg.top) if cfg.top else "",
                                           "-l 'complete genome'" if cfg.complete_genomes else "",
                                           "-f 'genomic.fna.gz'",
                                           "-t " + str(cfg.threads),
                                           "-o " + files_output_folder,
                                           "-M " + cfg.taxonomy if cfg.taxonomy else "",
                                           "-m",
                                           "-i" if resume_download else "",
                                           "-s" if cfg.quiet else "",
                                           "-w" if not cfg.verbose else "",
                                           cfg.genome_updater if cfg.genome_updater else ""])
        run(run_genome_updater_cmd, quiet=cfg.quiet)
        print_log(" - done in " + str("%.2f" % (time.time() - tx)) + "s.\n", cfg.quiet)
        save_state("build_download", files_output_folder)

    # get current version from assembly_summary
    input_folder = files_output_folder + get_gu_current_version(assembly_summary) + "/files/"

    build_custom_params = {"input": input_folder,
                           "input_extension": "fna.gz",
                           "input_target": "file",
                           "level": "assembly",
                           "ncbi_file_info": assembly_summary}

    build_default_params = {"db_prefix": cfg.db_prefix,
                            "taxonomy": cfg.taxonomy,
                            "threads": cfg.threads,
                            "max_fp": cfg.max_fp,
                            "filter_size": cfg.filter_size,
                            "kmer_size": cfg.kmer_size,
                            "window_size": cfg.window_size,
                            "hash_functions": cfg.hash_functions,
                            "verbose": cfg.verbose,
                            "quiet": cfg.quiet,
                            "ganon_path": cfg.ganon_path,
                            "n_refs": cfg.n_refs,
                            "n_batches": cfg.n_batches}

    build_custom_params.update(build_default_params)

    build_custom_config = Config("build-custom", **build_custom_params)
    save_config(build_custom_config, files_output_folder + "config.pkl")

    ret_build = build_custom(cfg=build_custom_config,
                             which_call="build")

    if ret_build:
        print_log("", cfg.quiet)
        print_log(files_output_folder + " contains reference sequences and configuration files.", cfg.quiet)
        print_log("Keep this folder if you want to update your database later. Otherwise it can be deleted.", cfg.quiet)
        print_log("", cfg.quiet)

    return ret_build


def update(cfg):
    files_output_folder = set_output_folder(cfg.db_prefix)
    if cfg.restart:
        restart_update(files_output_folder)

    tx = time.time()
    # Skip if already finished download from previous run
    if load_state("update_download", files_output_folder):
        print_log("Download finished - skipping", cfg.quiet)
    else:
        print_log("Downloading updated files", cfg.quiet)
        run_genome_updater_cmd = " ".join([cfg.path_exec['genome_updater'],
                                           "-o " + files_output_folder,
                                           "-m",
                                           "-s" if cfg.quiet else "",
                                           "-w" if not cfg.verbose else ""])
        run(run_genome_updater_cmd, quiet=cfg.quiet)
        print_log(" - done in " + str("%.2f" % (time.time() - tx)) + "s.\n", cfg.quiet)
        save_state("update_download", files_output_folder)

    # get current version from assembly_summary
    assembly_summary = files_output_folder + "assembly_summary.txt"
    input_folder = files_output_folder + get_gu_current_version(assembly_summary) + "/files/"

    build_custom_params = {"input": input_folder,
                           "input_extension": "fna.gz",
                           "input_target": "file",
                           "level": "assembly",
                           "ncbi_file_info": assembly_summary}

    build_default_params = {"db_prefix": cfg.output_db_prefix if cfg.output_db_prefix else cfg.db_prefix,
                            "threads": cfg.threads,
                            "verbose": cfg.verbose,
                            "quiet": cfg.quiet,
                            "ganon_path": cfg.ganon_path,
                            "n_refs": cfg.n_refs,
                            "n_batches": cfg.n_batches}
    build_custom_params.update(build_default_params)

    loaded_params = load_config(files_output_folder + "config.pkl")
    build_custom_params["taxonomy"] = loaded_params["taxonomy"]
    build_custom_params["max_fp"] = loaded_params["max_fp"]
    build_custom_params["filter_size"] = loaded_params["filter_size"]
    build_custom_params["kmer_size"] = loaded_params["kmer_size"]
    build_custom_params["window_size"] = loaded_params["window_size"]
    build_custom_params["hash_functions"] = loaded_params["hash_functions"]

    build_custom_config = Config("build-custom", **build_custom_params)

    ret_build = build_custom(cfg=build_custom_config,
                             which_call="update")

    if ret_build:
        if cfg.output_db_prefix:
            # Move files folder to new output_db_prefix
            os.rename(set_output_folder(cfg.db_prefix), set_output_folder(cfg.output_db_prefix))

        # Save config again (change on db_prefix, input folders)
        save_config(build_custom_config, files_output_folder + "config.pkl")

    return ret_build


def build_custom(cfg, which_call: str="build_custom"):
    files_output_folder = set_output_folder(cfg.db_prefix)

    # calling build_custom internally, already checked folders
    if which_call == "build_custom" and cfg.restart:
        restart_build(files_output_folder)

    build_output_folder = files_output_folder + "build/"        # DB_PREFIX_files/build/
    # Skip if already finished target_info from previous run
    if load_state(which_call + "_parse", files_output_folder):
        print_log("Parse finished - skipping", cfg.quiet)
    else:
        tax = None
        input_files = []
        target_info_file = build_output_folder + "target_info.tsv"  # DB_PREFIX_files/build/target_info.tsv

        # Create tmp build folder if not yet existing
        os.makedirs(build_output_folder, exist_ok=True)

        # Retrieve and check input files or folders
        if cfg.input:
            input_files = validate_input_files(cfg.input, cfg.input_extension, cfg.quiet)
            if not input_files:
                print_log("ERROR: No valid input files found")
                return False

        # Set --input-target automatically if not given
        if not cfg.input_target:
            # file is the default if more than one file is provided
            if len(input_files) > 1 or cfg.input_file:
                cfg.input_target = "file"
            else:
                cfg.input_target = "sequence"

        # Set-up taxonomy
        if cfg.taxonomy != "skip":
            tax = load_taxonomy(cfg, build_output_folder)

        # Set-up input info
        info = load_input(cfg, input_files)
        if info.empty:
            print_log("ERROR: Unable to parse input files")
            return False

        # Retrieve target info if taxonomy or specialization is required (and if file is not provided)
        if (tax or cfg.level == "assembly") and not cfg.input_file:
            if cfg.input_target == "sequence":
                get_sequence_info(cfg, info, tax, build_output_folder)
            else:
                get_file_info(cfg, info, tax, build_output_folder)

        # Validate taxonomic node only if taxonomy is provided
        if tax:
            validate_taxonomy(info, tax, cfg)
            if info.empty:
                print_log("ERROR: Unable to match taxonomy to targets")
                return False

        # Validate specialization for assembly and custom (required to be after taxonomy)
        if cfg.level in cfg.choices_level:
            validate_specialization(info, cfg.quiet)
            if info.empty:
                print_log("ERROR: Unable to match specialization to targets")
                return False

        # Define user bins for writing taxonomy and target info file
        user_bins_col = "target"  # Default as target
        if cfg.level in cfg.choices_level:
            user_bins_col = "specialization"  # if specialization was requested
        elif cfg.level:  # if any other level is provided (leaves, species, ...)
            user_bins_col = "node"

        # Filter and write taxonomy
        if tax:
            tax.filter(info["node"].unique())  # filter only used tax. nodes
            write_tax(cfg.db_prefix + ".tax", info, tax, user_bins_col, cfg.level, cfg.input_target)

        print(info)

        # Write aux file for ganon-build
        write_target_info(info, cfg.input_target, user_bins_col, target_info_file)
        save_state(which_call + "_parse", files_output_folder)

    # Skip if already finished target_info from previous run
    if load_state(which_call + "_run", files_output_folder):
        print_log("Build finished - skipping", cfg.quiet)
    else:
        # run ganon-build
        print("RUN BUILD")
        with open(cfg.db_prefix + ".ibf", "w") as tmpfile:
            print("dummy temp IBF for tests", file=tmpfile)
        save_state(which_call + "_run", files_output_folder)

    # Set output database files
    db_files_ext = ["ibf"] if cfg.taxonomy == "skip" else ["ibf", "tax"]
    print_log("Database: " + ", ".join([cfg.db_prefix + "." + e for e in db_files_ext]), cfg.quiet)
    if all([check_file(cfg.db_prefix + "." + e) for e in db_files_ext]):
        if which_call == "build_custom":
            # remove temporary files folder
            shutil.rmtree(files_output_folder)
        else:
            # remove tmp build folder
            shutil.rmtree(build_output_folder, ignore_errors=True)
            # remove save states
            clear_states(which_call, files_output_folder)
        print_log("Build finished successfully", cfg.quiet)
        return True
    else:
        print_log("ERROR: build failed - one or more database files not found or empty", cfg.quiet)
        return False


########################################################################################################################


def parse_input_file(input_file, info, input_target):
    """
    parse user provided --input-file with all specifications for input
    """
    info = pd.read_csv(input_file,
                       sep="\t",
                       header=None,
                       skiprows=0,
                       dtype=object,
                       names=["file", "target", "node", "specialization", "specialization_name"])

    # If no target was provided and target is file, use filename
    if info["target"].isna().all() and input_target == "file":
        info["target"] = info["file"].apply(os.path.basename)

    return info


def load_input(cfg, input_files):
    """
    Load basic target info, either provided as --target-info
    or extracted from file/sequences
    """
    tx = time.time()
    info = pd.DataFrame(columns=["target", "node", "specialization", "specialization_name", "file"])

    # Parse/load info without setting index
    if cfg.input_file:
        print_log("Parsing --input-file " + cfg.input_file, cfg.quiet)
        info = parse_input_file(cfg.input_file, info, cfg.input_target)
    else:
        if cfg.input_target == "sequence":
            print_log("Parsing sequences from --input (" + str(len(input_files)) + " files)", cfg.quiet)
            info = parse_sequence_accession(input_files, info)
        else:
            print_log("Parsing --input (" + str(len(input_files)) + " files)", cfg.quiet)
            info = parse_file_accession(input_files, info)

    # Drop cols without values
    shape_tmp = info.shape[0]
    info.dropna(how="all", inplace=True)
    if shape_tmp - info.shape[0] > 0:
        print_log(" - " + str(shape_tmp - info.shape[0]) + " invalid entries skipped", cfg.quiet)

    # Drop cols without target
    shape_tmp = info.shape[0]
    info.dropna(subset=["target"], inplace=True)
    if shape_tmp - info.shape[0] > 0:
        print_log(" - " + str(shape_tmp - info.shape[0]) + " invalid targets skipped", cfg.quiet)

    # Drop duplicated target
    shape_tmp = info.shape[0]
    info.drop_duplicates(subset=['target'], inplace=True)
    if shape_tmp - info.shape[0] > 0:
        print_log(" - " + str(shape_tmp - info.shape[0]) + " duplicated targets skipped", cfg.quiet)

    # set target as index
    info.set_index('target', inplace=True)
    print_log(" - " + str(info.shape[0]) + " unique entries", cfg.quiet)
    print_log(" - done in " + str("%.2f" % (time.time() - tx)) + "s.\n", cfg.quiet)

    return info


def load_taxonomy(cfg, build_output_folder):
    """
    load/download chosen taxonomy from multitax
    """
    tx = time.time()

    if cfg.taxonomy_files:
        print_log("Parsing " + cfg.taxonomy + " taxonomy", cfg.quiet)
    else:
        print_log("Downloading and parsing " + cfg.taxonomy + " taxonomy", cfg.quiet)

    if cfg.taxonomy == "ncbi":
        tax = NcbiTx(files=cfg.taxonomy_files)
    elif cfg.taxonomy == "gtdb":
        tax = GtdbTx(files=cfg.taxonomy_files, output_prefix=build_output_folder)

    # If level is not in special targets or leaves and present in available ranks
    if cfg.level not in [None, "leaves"] + cfg.choices_level:
        if cfg.level not in set(tax._ranks.values()):
            print_log(" - " + cfg.level + " not found in taxonomic ranks, changing to --level 'leaves'", cfg.quiet)
            cfg.level = 'leaves'

    print_log(" - done in " + str("%.2f" % (time.time() - tx)) + "s.\n", cfg.quiet)
    return tax


def write_tax(tax_file, info, tax, user_bins_col, level, input_target):
    """
    write tabular taxonomy file .tax
    may include specialization as nodes
    """

    # Write filtered "standard" taxonomy
    rm_files(tax_file)
    tax.write(tax_file)

    # Add specialization if not using direct taxonomic nodes
    if user_bins_col != "node":
        # Set rank to level or input_target
        rank = level if level else input_target

        with open(tax_file, "a") as outf:
            for target, row in info.iterrows():
                t = row[user_bins_col] if user_bins_col != "target" else target
                n = row["specialization_name"] if user_bins_col == "specialization" else t
                print(t, row["node"], rank, n, sep="\t", end="\n", file=outf)


def write_target_info(info, input_target, user_bins_col, target_info_file):
    """
    write tabular file to be parsed by ganon-build with: file <tab> target [<tab> sequence]
    """
    with open(target_info_file, "w") as outf:
        for target, row in info.iterrows():
            t = row[user_bins_col] if user_bins_col != "target" else target
            if input_target == "sequence":
                print(row["file"], t, target, sep="\t", end="\n", file=outf)
            else:
                print(row["file"], t, sep="\t", end="\n", file=outf)


def validate_specialization(info, quiet):
    """
    validate specialization for each node
    each specialization can have only one parent node
    and invalid nodes
    """

    tx = time.time()
    print_log("Validating specialization", quiet)
    # if all entries are null, no specialization was retrieved
    if all(info.specialization.isna()):
        print_log(" - No specialization provided/retrieved", quiet)
    else:
        # check for invalid specialization entries
        idx_null_spec = info.specialization.isna()

        # get unique tuples node-specialization
        node_spec = info[['node', 'specialization']].drop_duplicates()

        # check for duplicated specialization in the tuples
        idx_multi_parent_spec = info.specialization.isin(node_spec.specialization[node_spec.specialization.duplicated(keep=False)].unique())

        # merge indices for invalid entries
        idx_replace = idx_null_spec | idx_multi_parent_spec

        if idx_replace.any():
            # replace invalid specialization entries with target
            info.loc[idx_replace, "specialization"] = info.index[idx_replace]
            info.loc[idx_replace, "specialization_name"] = info.index[idx_replace]
            print_log(str(sum(idx_replace)) + " invalid specialization entries replaced by target\n", quiet)

    # Skip invalid nodes
    shape_tmp = info.shape[0]
    info.dropna(subset=["specialization"], inplace=True)
    if shape_tmp - info.shape[0] > 0:
        print_log(" - " + str(shape_tmp - info.shape[0]) + " entries without valid specialization skipped", quiet)

    # Fill names not provided with specialization
    info["specialization_name"].fillna(info["specialization"], inplace=True)

    print_log(" - done in " + str("%.2f" % (time.time() - tx)) + "s.\n", quiet)


def validate_taxonomy(info, tax, cfg):
    """
    validate taxonomy: convert to latest nodes (tax.latest)
    and chosen level (tax.parent_rank)
    """
    tx = time.time()
    print_log("Validating taxonomy", cfg.quiet)

    # Get latest and valid taxonomic nodes
    info["node"] = info["node"].apply(tax.latest)

    # If level is set and not leaves or reserved
    if cfg.level and cfg.level not in ["leaves"] + cfg.choices_level:
        info["node"] = info["node"].apply(lambda n: tax.parent_rank(n, cfg.level))

    # Skip invalid nodes (na == tax.undefined_node (None))
    shape_tmp = info.shape[0]
    info.dropna(subset=["node"], inplace=True)
    if shape_tmp - info.shape[0] > 0:
        print_log(" - " + str(shape_tmp - info.shape[0]) + " entries without valid taxonomic nodes skipped", cfg.quiet)

    print_log(" - done in " + str("%.2f" % (time.time() - tx)) + "s.\n", cfg.quiet)


def get_gu_current_version(assembly_summary):
    """
    return current version from genome_updater
    """
    return os.path.dirname(os.readlink(assembly_summary))


def restart_build(fld):
    """
    delete temporary folder to start build from scratch
    """
    shutil.rmtree(fld)
    os.makedirs(fld)


def restart_update(fld):
    """
    delete save states to start update from scratch
    """
    clear_states("update", fld)


def clear_states(prefix, folder):
    """
    delete all build/update save states
    """
    rm_files([folder + prefix + "_download",
              folder + prefix + "_parse",
              folder + prefix + "_run"])


def save_config(cfg, config_file):
    """
    save configuration for updates based on an instance of the Config class
    """
    v = vars(cfg)
    v["version"] = cfg.version
    with open(config_file, "wb") as file:
        pickle.dump(v, file)


def load_config(config_file):
    """
    load configuration
    """
    return pickle.load(open(config_file, "rb"))
