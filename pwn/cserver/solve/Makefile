# a make file for the test.c file

CC = g++
CFLAGS = -Wall
LDFLAGS =

all: chall

chall: chall.o
	$(CC) $(LDFLAGS) -o chall chall.o

chall.o: chall.cpp
	$(CC) $(CFLAGS) -c chall.cpp

clean:
	rm -f chall chall.o