#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <assert.h>

#define MAX_FILE_SIZE 4096

void win(){
    system("/bin/sh");
}

__attribute__((always_inline)) static inline size_t lcp(const char* a, const char* b, const char* up_to){
    size_t result = 0;
    assert(a > b);
    while(result < 255 && a != up_to && *a == *b){
        result++;

        a++;
        b++;
    }

    return result;
}

__attribute__((always_inline)) static inline void add_single_character(char* dst, char c){
    dst[0] = 0;
    dst[1] = c;
}

__attribute__((always_inline)) static inline void add_pair(char* dst, char offset, char size){
    dst[0] = offset;
    dst[1] = size;
}

int compress(const char* src, char* dst, size_t size){
    const char* start = dst;
    const char* src_end = src + size;

    // Bootstrap compression
    add_single_character(dst, src[0]);
    dst += 2;

    for(const char* p = src+1; p != src_end;){
        const char* best_find = NULL;
        size_t best_size = 0;

        for(const char* q = p-1; q >= src && q > (p-256); q--){
            size_t tmp = lcp(p, q, src_end);
            if(tmp > best_size){
                best_size = tmp;
                best_find = q;
            }
        }

        if(best_size == 0){
            add_single_character(dst, p[0]);
            p += 1;
        }
        else{
            add_pair(dst, (char)(p-best_find), (char)best_size);
            p += best_size;
        }

        dst += 2;
    }

    return (dst - start);
}

void chall(){
    size_t size;

    char size_buffer[5];
    char output_buffer[MAX_FILE_SIZE];
    char input_buffer[MAX_FILE_SIZE];

    memset(size_buffer, 0, 5);

    if (fgets(size_buffer, 5, stdin) != size_buffer){
        puts("Error reading size");
        exit(1);
    }

    if(sscanf(size_buffer, "%lu", &size) != 1){
        puts("Error parsing size");
        exit(1);
    }

    if(size > MAX_FILE_SIZE || size == 0){
        puts("Size too big");
        exit(1);
    }

    size = size;

    memset(input_buffer, 0, MAX_FILE_SIZE);
    memset(output_buffer, 0, MAX_FILE_SIZE);

    if(fread(input_buffer, 1, size, stdin) != size){
        exit(2);
    }

    size_t new_size = compress(input_buffer, output_buffer, size);

    fwrite(output_buffer, 1, new_size, stdout);

}

int main(int argc, char** argv){
    setvbuf(stdin, 0, 0, 0);
    setvbuf(stdout, 0, 0, 0);
    setvbuf(stderr, 0, 0, 0);

    chall();

    return 0;
}