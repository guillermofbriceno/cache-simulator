#!/usr/bin/python3

import sys
import math
import argparse

class Cache:
    def __init__(self, block_size, cache_size, num_ways, data_type):
        # initializes cache tag list: rows represent block sets, columns represent ways
        self.num_blocks = int(cache_size / block_size)
        self.num_sets = int(self.num_blocks / num_ways)
        self.cache_ways_tags = [[] for i in range(self.num_sets)]
        self.num_ways = num_ways
        self.data_type = data_type

        # initializes the LRU bits list for every block on each way, as the max integer num_ways - 1
        # lru list is useless when num_ways = 1 (direct mapped)
        self.lru_bits = [[] for i in range(self.num_sets)]
        for index, block_set in enumerate(self.lru_bits):
            self.lru_bits[index] = [i for i in range(num_ways)] 
            self.cache_ways_tags[index] = [-1 for i in range(num_ways)]

        # the following designates offset, index, and tag string indexes from left-0 to right
        temp_index_bits = math.frexp(self.num_sets)[1] - 1
        temp_offset_bits = math.frexp(block_size)[1] - 1
        self.tag_bits = [0, 32 - (temp_offset_bits + temp_index_bits)]
        self.index_bits = [self.tag_bits[1], self.tag_bits[1] + temp_index_bits]
        self.offset_bits = [self.index_bits[1], self.index_bits[1] + temp_offset_bits]

        self.hits = 0
        self.misses = 0

    def request(self, address):
        address = address.rstrip()

        # get the tag and index from address as integers
        tag = get_from_bitrange(self.tag_bits, address)
        index = get_from_bitrange(self.index_bits, address)

        tag_set = self.cache_ways_tags[index]
        if tag in tag_set:
            self.hits += 1
            #print(address, tag, index, "hit")
            self.update_lru(index, tag_set.index(tag), 'h')
        else:
            self.misses += 1
            #print(address, tag, index, "miss")
            self.replace(tag, index)

    def replace(self, tag, index):
        lru_set = self.lru_bits[index]
        tag_set = self.cache_ways_tags[index]

        for way, value in enumerate(lru_set):
            if value == self.num_ways - 1:
                tag_set[way] = tag
                self.update_lru(index, way, 'm')
                break

        self.cache_ways_tags[index] = tag_set

    def update_lru(self, index, requested_way, hit_or_miss):
        lru_set = self.lru_bits[index]

        temp_set = lru_set
        temp_value = temp_set[requested_way]

        if hit_or_miss == 'm':
            for way in range(self.num_ways):
                if way == requested_way:
                    temp_set[way] = 0
                else:
                    temp_set[way] += 1
        elif hit_or_miss == 'h':
            for way in range(self.num_ways):
                if temp_value == self.num_ways - 1:
                    if way == requested_way:
                        temp_set[way] = 0
                    else:
                        temp_set[way] += 1
                elif temp_value == 0:
                    break
                else:
                    if temp_value > temp_set[way]:
                        temp_set[way] += 1
                    elif way == requested_way:
                        temp_set[way] = 0

        self.lru_bits[index] = temp_set

    def print_debug_stats(self):
        print("Cache Type:", "\t\t", self.data_type)
        print("Tag bit width:", "\t\t", self.tag_bits[1] - self.tag_bits[0])
        print("Index bit width:","\t", self.index_bits[1] - self.index_bits[0])
        print("Number of sets:", "\t", len(self.cache_ways_tags))
        print("Number of blocks:", "\t", self.num_blocks)
        print("Hits:", "\t\t\t", self.hits)
        print("Misses:", "\t\t", self.misses)
        print("Hitrate:", "\t\t", '{0:.04f}'.format(self.hits/(self.hits+self.misses)))
        print("Missrate:", "\t\t", '{0:.04f}'.format(1 - self.hits/(self.hits+self.misses)), "\n")

    def print_debug_blocks(self):
        print("---Tag and LRU list print---")
        for tag_set, lru_set in zip(self.cache_ways_tags, self.lru_bits):
            print(lru_set, tag_set)

def get_from_bitrange(bit_range, hex_val):
    left_bit, right_bit = bit_range
    binary_string = "{0:032b}".format(int(hex_val, 16)) # hex to bin
    cut_string = binary_string[left_bit:right_bit]
    return 0 if (left_bit - right_bit) == 0 else int(cut_string, 2)

def init_cache(args):
    is_unified = args.isize is None

    if not is_unified:
        icache = Cache(args.ibsize, args.isize, args.iassoc, "inst")
        dcache = Cache(args.dbsize, args.dsize, args.dassoc, "data")
    else:
        ucache = Cache(args.ubsize, args.usize, args.uassoc, "unified")

    return [ucache] if is_unified else [icache, dcache]

def cache_multiplexer(req_type, address, icache, dcache):
    if req_type == "1" or  req_type == "0":
        dcache.request(address)
    elif req_type == "2":
        icache.request(address)
    else:
        print("Reached invalid trace request", req_type)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-isize", help="Size of instruction cache in bytes", type=int)
    parser.add_argument("-ibsize", help="Size of instruction cache blocks in bytes", type=int)
    parser.add_argument("-iassoc", help="Associativity of instruction cache", type=int)
    parser.add_argument("-dsize", help="Size of data cache in bytes", type=int)
    parser.add_argument("-dbsize", help="Size of data cache blocks in bytes", type=int)
    parser.add_argument("-dassoc", help="Associativity of data cache", type=int)
    parser.add_argument("-usize", help="Size of unified cache in bytes", type=int)
    parser.add_argument("-ubsize", help="Size of unified cache in bytes", type=int)
    parser.add_argument("-uassoc", help="Associativity of unified cache", type=int)
    parser.add_argument("-trace", help="Input trace file")
    args = parser.parse_args()

    if (args.isize is not None or args.dsize is not None) and (args.usize is not None):
        print("Gave both unified and split cache arguments. Exit.")
        sys.exit()

    caches = init_cache(args)
    is_split_cache = True if len(caches) == 2 else False


    with open(args.trace) as trace:
        print("Starting Simulator...\n")
        for request in trace:
            req_type, address = request.split(" ")

            if is_split_cache:
                cache_multiplexer(req_type, address, caches[0], caches[1])
            else:
                caches[0].request(address)

    for cache in caches:
        cache.print_debug_stats()

if __name__ == "__main__":
    main()
