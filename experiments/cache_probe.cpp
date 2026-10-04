#include <algorithm>
#include <chrono>
#include <cstdint>
#include <cstdlib>
#include <iostream>
#include <numeric>
#include <random>
#include <stdexcept>
#include <string>
#include <thread>
#include <vector>

// A controlled memory-access probe. Each worker owns its array, so the
// measured contention comes from the shared cache/memory hierarchy.
int main(int argc, char** argv) {
    if (argc != 7) {
        std::cerr << "usage: cache_probe PATTERN BYTES STRIDE_BYTES ACCESSES THREADS SEED\n"
                     "PATTERN: sequential | strided | random | conflict\n";
        return 2;
    }
    try {
        const std::string pattern = argv[1];
        const auto bytes = std::stoull(argv[2]);
        const auto stride_bytes = std::stoull(argv[3]);
        const auto accesses = std::stoull(argv[4]);
        const auto threads = std::stoull(argv[5]);
        const auto seed = std::stoull(argv[6]);
        if (pattern != "sequential" && pattern != "strided" &&
            pattern != "random" && pattern != "conflict")
            throw std::invalid_argument("unknown pattern");
        if (bytes < 64 || bytes % 64 || stride_bytes < 64 || stride_bytes % 64 ||
            accesses == 0 || threads == 0 || threads > 64)
            throw std::invalid_argument("bytes/stride must be multiples of 64; accesses and threads must be positive");

        const size_t lines = bytes / 64;
        const size_t step = stride_bytes / 64;
        std::vector<uint64_t> sums(threads, 0);
        std::vector<std::thread> workers;
        const auto start = std::chrono::steady_clock::now();
        auto run_worker = [&](size_t worker) {
                // Eight uint64_t values per 64-byte line. The allocation is
                // aligned so conflict probes map predictably to cache sets.
                std::vector<uint64_t> storage(bytes / sizeof(uint64_t) + 8);
                auto* data = reinterpret_cast<uint64_t*>(
                    (reinterpret_cast<uintptr_t>(storage.data()) + 63) & ~uintptr_t(63));
                for (size_t i = 0; i < bytes / sizeof(uint64_t); ++i)
                    data[i] = static_cast<uint64_t>(i + worker + 1);
                std::vector<size_t> order;
                if (pattern == "random") {
                    order.resize(lines);
                    std::iota(order.begin(), order.end(), 0);
                    std::mt19937_64 rng(seed + worker);
                    std::shuffle(order.begin(), order.end(), rng);
                }
                uint64_t sum = 0;
                for (uint64_t n = 0; n < accesses; ++n) {
                    const size_t line = pattern == "random" ? order[n % lines]
                        : pattern == "sequential" ? n % lines
                        : (n * step) % lines;
                    sum += data[line * 8];
                }
                sums[worker] = sum;
        };
        // The main thread is one of the workers; no spare simulated core is
        // needed just to wait for joins.
        for (size_t worker = 1; worker < threads; ++worker)
            workers.emplace_back(run_worker, worker);
        run_worker(0);
        for (auto& worker : workers) worker.join();
        const auto elapsed = std::chrono::duration<double>(
            std::chrono::steady_clock::now() - start).count();
        uint64_t checksum = 0;
        for (auto value : sums) checksum += value;
        std::cout << "pattern=" << pattern << " bytes_per_thread=" << bytes
                  << " stride_bytes=" << stride_bytes << " accesses_per_thread=" << accesses
                  << " threads=" << threads << " seed=" << seed
                  << " checksum=" << checksum << " native_seconds=" << elapsed << '\n';
    } catch (const std::exception& e) {
        std::cerr << "invalid arguments: " << e.what() << '\n';
        return 2;
    }
}
