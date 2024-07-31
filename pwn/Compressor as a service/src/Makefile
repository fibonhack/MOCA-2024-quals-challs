# Compiler
CC = gcc

# Compiler flags
CFLAGS = -no-pie -fno-stack-protector

# Target executable name
TARGET = chall

# Source file
SRC = chall.c

# Default rule to build the target
all: $(TARGET)

# Rule to build the target executable
$(TARGET):
	$(CC) $(CFLAGS) -o $(TARGET) $(SRC)

# Rule to clean up generated files
clean:
	rm -f $(TARGET)

# Phony targets
.PHONY: all clean