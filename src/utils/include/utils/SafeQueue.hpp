#pragma once

#include <condition_variable>
#include <mutex>
#include <queue>

template < class T >
class SafeQueue
{

private:
    std::queue< T >         q;
    std::mutex              m;
    int                     max_size;
    bool                    push_over = false;
    std::condition_variable cv_push;
    std::condition_variable cv_pop;

public:
    SafeQueue()
    {
        max_size = -1; // no limit
    }

    SafeQueue( int max )
    {
        max_size = max;
    }

    void set_max_size( int max )
    {
        std::lock_guard< std::mutex > lock( m );
        max_size = max;
    }

    void push( T t )
    {
        std::unique_lock< std::mutex > lock( m );
        while ( q.size() >= max_size )
            cv_push.wait( lock );
        q.push( t );
        cv_pop.notify_one();
    }

    T pop()
    {
        std::unique_lock< std::mutex > lock( m );
        while ( q.size() == 0 )
        {
            if ( push_over )
                return T();
            cv_pop.wait( lock );
        }
        T val = q.front();
        q.pop();
        cv_push.notify_one();
        return val;
    }

    void notify_push_over()
    {
        std::lock_guard< std::mutex > lock( m );
        push_over = true;
        cv_pop.notify_all();
    }

    int size()
    {
        std::lock_guard< std::mutex > lock( m );
        return q.size();
    }

    bool empty()
    {
        std::lock_guard< std::mutex > lock( m );
        return q.empty();
    }
};
