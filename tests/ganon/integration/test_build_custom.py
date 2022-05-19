import unittest
import sys

sys.path.append('src')
from ganon import ganon
from ganon.config import Config

base_dir = "tests/ganon/"
sys.path.append(base_dir)
from utils import setup_dir
from utils import list_files_folder
from utils import list_sequences
from utils import build_sanity_check_and_parse
data_dir = base_dir + "data/"


class TestBuildCustom(unittest.TestCase):

    results_dir = base_dir + "results/integration/build-custom/"

    default_params = {"input": data_dir + "build-custom/files/",
                      "taxonomy": "skip",
                      "threads": 1,
                      "write_info_file": True,
                      "keep_files": True,
                      "verbose": True,
                      "quiet": True}

    @classmethod
    def setUpClass(self):
        setup_dir(self.results_dir)

    def test_input_folder(self):
        """
        ganon build-custom with folder as --input with --extension
        """
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_input_folder"
        params["input"] = data_dir + "build-custom/files/"
        params["input_extension"] = "fna.gz"
        cfg = Config("build-custom", **params)
        self.assertTrue(ganon.main(cfg=cfg), "ganon build-custom run failed")
        res = build_sanity_check_and_parse(vars(cfg))
        self.assertIsNotNone(res, "ganon build-custom sanity check failed")

        files = list_files_folder(params["input"], params["input_extension"])
        self.assertTrue(res["target"]["file"].isin(files).all(), "Files missing from target")
        self.assertEqual(len(files), res["target"].shape[0], "Wrong number of files on target")
        self.assertTrue(res["info"]["file"].isin(files).all(), "Files missing from info")
        self.assertEqual(len(files), res["info"].shape[0], "Wrong number of files on info")

        # Wrong extension
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_input_folder_wrong_extension"
        params["input"] = data_dir + "build-custom/files/"
        params["input_extension"] = "xxx.gz"
        cfg = Config("build-custom", **params)
        self.assertFalse(ganon.main(cfg=cfg), "ganon build-custom ran but it should fail")

        # Wrong folder
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_input_folder_wrong_folder"
        params["input"] = data_dir + "wrong-place/"
        params["input_extension"] = "fna.gz"
        cfg = Config("build-custom", **params)
        self.assertFalse(ganon.main(cfg=cfg), "ganon build-custom ran but it should fail")

    def test_input_files(self):
        """
        ganon build-custom with files as --input
        """
        files = list_files_folder(data_dir + "build-custom/files/", "fna.gz")
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_input_files"
        params["input"] = files
        params["input_extension"] = ""
        cfg = Config("build-custom", **params)
        self.assertTrue(ganon.main(cfg=cfg), "ganon build-custom run failed")
        res = build_sanity_check_and_parse(vars(cfg))
        self.assertIsNotNone(res, "ganon build-custom sanity check failed")

        self.assertTrue(res["target"]["file"].isin(files).all(), "Files missing from target")
        self.assertEqual(len(files), res["target"].shape[0], "Wrong number of files on target")
        self.assertTrue(res["info"]["file"].isin(files).all(), "Files missing from info")
        self.assertEqual(len(files), res["info"].shape[0], "Wrong number of files on info")

        # All files are invalid
        files = [f+".xxx" for f in files]
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_input_files_invalid"
        params["input"] = files
        params["input_extension"] = ""
        cfg = Config("build-custom", **params)
        self.assertFalse(ganon.main(cfg=cfg), "ganon build-custom ran but it should fail")

    def test_input_folders_files(self):
        """
        ganon build-custom with files and folders as --input with --extension
        """
        files = list_files_folder(data_dir + "build-custom/files/", "fna.gz")
        folder = data_dir + "build-custom/files/more/"
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_input_folders_files"
        params["input"] = files + [folder]
        params["input_extension"] = "fna.gz"
        cfg = Config("build-custom", **params)
        self.assertTrue(ganon.main(cfg=cfg), "ganon build-custom run failed")
        res = build_sanity_check_and_parse(vars(cfg))
        self.assertIsNotNone(res, "ganon build-custom sanity check failed")

        files.extend(list_files_folder(folder, params["input_extension"]))
        self.assertTrue(res["target"]["file"].isin(files).all(), "Files missing from target")
        self.assertEqual(len(files), res["target"].shape[0], "Wrong number of files on target")
        self.assertTrue(res["info"]["file"].isin(files).all(), "Files missing from info")
        self.assertEqual(len(files), res["info"].shape[0], "Wrong number of files on info")

    def test_taxonomy(self):
        """
        ganon build-custom with --taxonomy ncbi,gtdb,skip
        """
        #ncbi
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_taxonomy_ncbi"
        params["taxonomy"] = "ncbi"
        params["taxonomy_files"] = data_dir + "build-custom/taxdump.tar.gz"
        params["ncbi_file_info"] = data_dir + "build-custom/assembly_summary.txt"
        cfg = Config("build-custom", **params)
        self.assertTrue(ganon.main(cfg=cfg), "ganon build-custom run failed")
        res = build_sanity_check_and_parse(vars(cfg))
        self.assertIsNotNone(res, "ganon build-custom sanity check failed")

        #gtdb
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_taxonomy_gtdb"
        params["taxonomy"] = "gtdb"
        params["taxonomy_files"] = [data_dir + "build-custom/ar53_taxonomy.tsv.gz",
                                    data_dir + "build-custom/bac120_taxonomy.tsv.gz"]
        cfg = Config("build-custom", **params)
        self.assertTrue(ganon.main(cfg=cfg), "ganon build-custom run failed")
        res = build_sanity_check_and_parse(vars(cfg))
        self.assertIsNotNone(res, "ganon build-custom sanity check failed")

        #skip
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_taxonomy_skip"
        params["taxonomy"] = "skip"
        params["taxonomy_files"] = ""
        cfg = Config("build-custom", **params)
        self.assertTrue(ganon.main(cfg=cfg), "ganon build-custom run failed")
        res = build_sanity_check_and_parse(vars(cfg))
        self.assertIsNotNone(res, "ganon build-custom sanity check failed")

    def test_input_target_file(self):
        """
        ganon build-custom with --input-target file
        """
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_input_target_file"
        params["input_target"] = "file"
        cfg = Config("build-custom", **params)
        self.assertTrue(ganon.main(cfg=cfg), "ganon build-custom run failed")
        res = build_sanity_check_and_parse(vars(cfg))
        self.assertIsNotNone(res, "ganon build-custom sanity check failed")

        files = list_files_folder(params["input"], "fna.gz")
        self.assertTrue(res["target"]["file"].isin(files).all(), "Files missing from target")
        self.assertEqual(len(files), res["target"].shape[0], "Wrong number of files on target")
        self.assertTrue(res["info"]["file"].isin(files).all(), "Files missing from info")
        self.assertEqual(len(files), res["info"].shape[0], "Wrong number of files on info")

    def test_input_target_sequence(self):
        """
        ganon build-custom with --input-target sequence
        """
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_input_target_sequence"
        params["input_target"] = "sequence"
        cfg = Config("build-custom", **params)
        self.assertTrue(ganon.main(cfg=cfg), "ganon build-custom run failed")
        res = build_sanity_check_and_parse(vars(cfg))
        self.assertIsNotNone(res, "ganon build-custom sanity check failed")

        sequences = list_sequences(list_files_folder(params["input"], "fna.gz"))
        self.assertTrue(res["target"]["sequence"].isin(sequences).all(), "Files missing from target")
        self.assertEqual(len(sequences), res["target"].shape[0], "Wrong number of files on target")
        self.assertTrue(res["info"]["target"].isin(sequences).all(), "Files missing from info")
        self.assertEqual(len(sequences), res["info"].shape[0], "Wrong number of files on info")

    def test_level_file_default(self):
        """
        ganon build-custom --input-target file and --level default
        """

        # --level default (file) - no tax
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_level_file_default"
        params["input_target"] = "file"
        cfg = Config("build-custom", **params)
        self.assertTrue(ganon.main(cfg=cfg), "ganon build-custom run failed")
        res = build_sanity_check_and_parse(vars(cfg))
        self.assertIsNotNone(res, "ganon build-custom sanity check failed")

        # --level default (file) NCBI
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_level_file_default_ncbi"
        params["input_target"] = "file"
        params["taxonomy"] = "ncbi"
        params["taxonomy_files"] = data_dir + "build-custom/taxdump.tar.gz"
        params["ncbi_file_info"] = data_dir + "build-custom/assembly_summary.txt"
        cfg = Config("build-custom", **params)
        self.assertTrue(ganon.main(cfg=cfg), "ganon build-custom run failed")
        res = build_sanity_check_and_parse(vars(cfg))
        self.assertIsNotNone(res, "ganon build-custom sanity check failed")

        # --level default (file) GTDB
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_level_file_default_gtdb"
        params["input_target"] = "file"
        params["taxonomy"] = "gtdb"
        params["taxonomy_files"] = [data_dir + "build-custom/ar53_taxonomy.tsv.gz",
                                    data_dir + "build-custom/bac120_taxonomy.tsv.gz"]
        cfg = Config("build-custom", **params)
        self.assertTrue(ganon.main(cfg=cfg), "ganon build-custom run failed")
        res = build_sanity_check_and_parse(vars(cfg))
        self.assertIsNotNone(res, "ganon build-custom sanity check failed")

    def test_level_file_taxrank(self):
        """
        ganon build-custom --input-target file and --level {taxonomic rank}
        """

        # --level genus NCBI
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_level_file_genus_ncbi"
        params["input_target"] = "file"
        params["level"] = "genus"
        params["taxonomy"] = "ncbi"
        params["taxonomy_files"] = data_dir + "build-custom/taxdump.tar.gz"
        params["ncbi_file_info"] = data_dir + "build-custom/assembly_summary.txt"
        cfg = Config("build-custom", **params)
        self.assertTrue(ganon.main(cfg=cfg), "ganon build-custom run failed")
        res = build_sanity_check_and_parse(vars(cfg))
        self.assertIsNotNone(res, "ganon build-custom sanity check failed")
        # Tax must not have "species" (filtered out)
        self.assertFalse("species" in res["tax"]._ranks.values(), "rank found")

        # --level genus GTDB
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_level_file_genus_gtdb"
        params["input_target"] = "file"
        params["level"] = "genus"
        params["taxonomy"] = "gtdb"
        params["taxonomy_files"] = [data_dir + "build-custom/ar53_taxonomy.tsv.gz",
                                    data_dir + "build-custom/bac120_taxonomy.tsv.gz"]
        cfg = Config("build-custom", **params)
        self.assertTrue(ganon.main(cfg=cfg), "ganon build-custom run failed")
        res = build_sanity_check_and_parse(vars(cfg))
        self.assertIsNotNone(res, "ganon build-custom sanity check failed")
        # Tax must not have "species" (filtered out)
        self.assertFalse("species" in res["tax"]._ranks.values(), "rank found")

    def test_level_file_leaves(self):
        """
        ganon build-custom --input-target file and --level leaves
        """

        # --level leaves NCBI
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_level_file_leaves_ncbi"
        params["input_target"] = "file"
        params["level"] = "leaves"
        params["taxonomy"] = "ncbi"
        params["taxonomy_files"] = data_dir + "build-custom/taxdump.tar.gz"
        params["ncbi_file_info"] = data_dir + "build-custom/assembly_summary.txt"
        cfg = Config("build-custom", **params)
        self.assertTrue(ganon.main(cfg=cfg), "ganon build-custom run failed")
        self.assertIsNotNone(build_sanity_check_and_parse(vars(cfg)), "ganon build-custom sanity check failed")

        # --level leaves GTDB
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_level_file_leaves_gtdb"
        params["input_target"] = "file"
        params["level"] = "leaves"
        params["taxonomy"] = "gtdb"
        params["taxonomy_files"] = [data_dir + "build-custom/ar53_taxonomy.tsv.gz",
                                    data_dir + "build-custom/bac120_taxonomy.tsv.gz"]
        cfg = Config("build-custom", **params)
        self.assertTrue(ganon.main(cfg=cfg), "ganon build-custom run failed")
        self.assertIsNotNone(build_sanity_check_and_parse(vars(cfg)), "ganon build-custom sanity check failed")

    def test_level_file_specialization(self):
        """
        ganon build-custom --input-target file and --level assembly/custom (specialization)
        """

        # --level assembly no tax
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_level_file_assembly"
        params["input_target"] = "file"
        params["level"] = "assembly"
        params["ncbi_file_info"] = data_dir + "build-custom/assembly_summary.txt"
        cfg = Config("build-custom", **params)
        self.assertTrue(ganon.main(cfg=cfg), "ganon build-custom run failed")
        self.assertIsNotNone(build_sanity_check_and_parse(vars(cfg)), "ganon build-custom sanity check failed")

        # --level assembly NCBI
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_level_file_assembly_ncbi"
        params["input_target"] = "file"
        params["level"] = "assembly"
        params["taxonomy"] = "ncbi"
        params["taxonomy_files"] = data_dir + "build-custom/taxdump.tar.gz"
        params["ncbi_file_info"] = data_dir + "build-custom/assembly_summary.txt"
        cfg = Config("build-custom", **params)
        self.assertTrue(ganon.main(cfg=cfg), "ganon build-custom run failed")
        self.assertIsNotNone(build_sanity_check_and_parse(vars(cfg)), "ganon build-custom sanity check failed")

        # --level assembly GTDB
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_level_file_assembly_gtdb"
        params["input_target"] = "file"
        params["level"] = "assembly"
        params["taxonomy"] = "gtdb"
        params["taxonomy_files"] = [data_dir + "build-custom/ar53_taxonomy.tsv.gz",
                                    data_dir + "build-custom/bac120_taxonomy.tsv.gz"]
        cfg = Config("build-custom", **params)
        self.assertTrue(ganon.main(cfg=cfg), "ganon build-custom run failed")
        self.assertIsNotNone(build_sanity_check_and_parse(vars(cfg)), "ganon build-custom sanity check failed")

        # --level custom NCBI
        # uses info.tsv from last tests
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_level_file_custom_ncbi"
        params["input"] = []
        params["input_target"] = "file"
        params["input_file"] = self.results_dir + "test_level_file_assembly_ncbi.info.tsv"
        params["level"] = "custom"
        params["taxonomy"] = "ncbi"
        params["taxonomy_files"] = data_dir + "build-custom/taxdump.tar.gz"
        cfg = Config("build-custom", **params)
        self.assertTrue(ganon.main(cfg=cfg), "ganon build-custom run failed")
        self.assertIsNotNone(build_sanity_check_and_parse(vars(cfg)), "ganon build-custom sanity check failed")

        # --level custom GTDB
        # uses info.tsv from last tests
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_level_file_custom_gtdb"
        params["input"] = []
        params["input_target"] = "file"
        params["input_file"] = self.results_dir + "test_level_file_assembly_gtdb.info.tsv"
        params["level"] = "custom"
        params["taxonomy"] = "gtdb"
        params["taxonomy_files"] = [data_dir + "build-custom/ar53_taxonomy.tsv.gz",
                                    data_dir + "build-custom/bac120_taxonomy.tsv.gz"]
        cfg = Config("build-custom", **params)
        self.assertTrue(ganon.main(cfg=cfg), "ganon build-custom run failed")
        self.assertIsNotNone(build_sanity_check_and_parse(vars(cfg)), "ganon build-custom sanity check failed")

    def test_level_sequence_default(self):
        """
        ganon build-custom --input-target sequence and --level default
        """
        # --level default (sequence) - no tax
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_level_sequence_default"
        params["input_target"] = "sequence"
        cfg = Config("build-custom", **params)
        self.assertTrue(ganon.main(cfg=cfg), "ganon build-custom run failed")
        res = build_sanity_check_and_parse(vars(cfg))
        self.assertIsNotNone(res, "ganon build-custom sanity check failed")

        # --level default (sequence) - NCBI
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_level_sequence_default_ncbi"
        params["input_target"] = "sequence"
        params["taxonomy"] = "ncbi"
        params["taxonomy_files"] = data_dir + "build-custom/taxdump.tar.gz"
        params["ncbi_sequence_info"] = data_dir + "build-custom/nucl_gb.accession2taxid.gz"
        cfg = Config("build-custom", **params)
        self.assertTrue(ganon.main(cfg=cfg), "ganon build-custom run failed")
        res = build_sanity_check_and_parse(vars(cfg))
        self.assertIsNotNone(res, "ganon build-custom sanity check failed")

    def test_level_sequence_taxrank(self):
        """
        ganon build-custom --input-target sequence and --level {tax.rank}
        """
        # --level genus NCBI
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_level_sequence_genus_ncbi"
        params["input_target"] = "sequence"
        params["level"] = "genus"
        params["taxonomy"] = "ncbi"
        params["taxonomy_files"] = data_dir + "build-custom/taxdump.tar.gz"
        params["ncbi_sequence_info"] = data_dir + "build-custom/nucl_gb.accession2taxid.gz"
        cfg = Config("build-custom", **params)
        self.assertTrue(ganon.main(cfg=cfg), "ganon build-custom run failed")
        res = build_sanity_check_and_parse(vars(cfg))
        self.assertIsNotNone(res, "ganon build-custom sanity check failed")
        # Tax must not have "species" (filtered out)
        self.assertFalse("species" in res["tax"]._ranks.values(), "rank found")

    def test_level_sequence_leaves_ncbi(self):
        """
        ganon build-custom --input-target sequence and --level leaves
        """
        # --level leaves NCBI
        params = self.default_params.copy()
        params["db_prefix"] = self.results_dir + "test_level_sequence_leaves_ncbi"
        params["input_target"] = "sequence"
        params["level"] = "leaves"
        params["taxonomy"] = "ncbi"
        params["taxonomy_files"] = data_dir + "build-custom/taxdump.tar.gz"
        params["ncbi_sequence_info"] = data_dir + "build-custom/nucl_gb.accession2taxid.gz"
        cfg = Config("build-custom", **params)
        self.assertTrue(ganon.main(cfg=cfg), "ganon build-custom run failed")
        res = build_sanity_check_and_parse(vars(cfg))
        self.assertIsNotNone(res, "ganon build-custom sanity check failed")

    def test_ncbi_sequence_info(self):
        """
        ganon build-custom --ncbi-sequence-info files
        """
        # Test with one, two or invalid file
        pass

    def test_ncbi_file_info(self):
        """
        ganon build-custom --ncbi-file-info files
        """
        # Test with one, two or invalid file
        pass

    def test_restart(self):
        """
        ganon build-custom --restart
        """
        pass


if __name__ == '__main__':
    unittest.main()
