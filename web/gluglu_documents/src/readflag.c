#include <stdio.h>

int main() {
    char *flag;
    size_t len = 0;

    FILE *f = fopen("/flag.txt", "r");
    if (f == NULL) {
        printf("flag.txt not found\n");
        return 1;
    }

    if (getline(&flag, &len, f) != -1){
        printf("flag: %s\n", flag);
        fflush(stdout);
        free(flag);
    }else{
        puts("Error reading flag");
    }

    fclose(f);
    return 0;
}