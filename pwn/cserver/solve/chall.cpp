#include <unistd.h>
#include <sys/select.h>
#include <sys/types.h>
#include <sys/socket.h>
#include <sys/un.h>

#include <algorithm>
#include <cstdio>
#include <iostream>
#include <string>
#include <vector>
#include <set>

using namespace std;

int read_line(int fd, char *buf, int size, bool drop_newline = false) {
    memset(buf, 0, size);
    int n = 0;
    while (n < size-1) {
        int r = read(fd, buf + n, 1);
        // printf("buf: %s\n", buf);
        if (r == -1) {
            perror("read()");
            return -1;
        }
        if (r == 0) {
            break;
        }
        n++;
        if (buf[n-1] == '\n') {
            break;
        }
    }
    buf[n] = '\0';
    if (drop_newline && n > 0 && buf[n-1] == '\n') {
        buf[n-1] = '\0';
    }
    return n;
}

int write_line(int fd, char *buf) {
    int r = write(fd, buf, strlen(buf));
    if (r == -1) {
        perror("write()");
        return -1;
    }
    r = write(fd, "\n", 1);
    if (r == -1) {
        perror("write()");
        return -1;
    }
    return r;
}

int handle(int fd, set<int> &fds, set<int> &rfds_copy, int &maxfd, fd_set &rfds) {
    char buf[1024];
    while (1) {
        // cout << "Server: I am waiting for a message!" << endl;
        int n = read_line(fd, buf, 1024, true);
        cout << "Server: I received " << buf << endl;
        if (n <= 0) {
            // cout << "Server: connection closed by peer!" << fd << endl;
            rfds_copy.erase(fd);
            fds.erase(fd);
            close(fd);
            if (fd == maxfd) {
                maxfd = *max_element(rfds_copy.begin(), rfds_copy.end());
                // cout << "Server: new maxfd: " << maxfd << endl;
            }
            return -1;
        }
        if (strcmp(buf, "Exit") == 0) {
            return -2;
        }
        if (strcmp(buf, "Close") == 0) {
            // cout << "Server: I am closing the connection! " << fd << endl;
            rfds_copy.erase(fd);
            fds.erase(fd);
            close(fd);
            if (fd == maxfd) {
                maxfd = *max_element(rfds_copy.begin(), rfds_copy.end());
                // cout << "Server: new maxfd: " << maxfd << endl;
            }
            return -1;
        }
        if (strcmp(buf, "Save") == 0) {
            // cout << "Server: Saving connection!" << endl;
            rfds_copy.erase(fd);
            fds.insert(fd);
            return 0;
        }
        if (strcmp(buf, "Hello") == 0) {
            // cout << "Server: monitoring! " << fd << endl;
            rfds_copy.insert(fd);
            if (fd > maxfd) {
                // cout << "Server: old maxfd: " << maxfd << endl;
                maxfd = fd;
                // cout << "Server: new maxfd: " << maxfd << endl;
            }
            return 1;
        }
        // check buf is a number then return that number
        // use stoi and catch exception invalid_argument
        string str(buf);
        if (std::all_of(str.begin(), str.end(), ::isdigit)) {
            try {
                int num = stoi(buf);
                if (fds.count(num) == 0) {
                    cout << "Server: I don't have that connection! " << num << endl;
                    return -1;
                }
                // cout << "Server: monitoring! " << num << endl;
                rfds_copy.insert(num);
                if (num > maxfd) {
                    // cout << "Server: old maxfd: " << maxfd << endl;
                    maxfd = num;
                    // cout << "Server: new maxfd: " << maxfd << endl;
                }
            } catch (invalid_argument const& e){
            }
        }
    }
}

int server(int server_socket) {
    int n;

    int fd;
    
    struct sockaddr_un client_addr;
    socklen_t clen = sizeof(client_addr);

    set<int> fds;
    set<int> rfds_copy;

    int maxfd = server_socket;
    bool running = true;

    fd_set rfds;

    rfds_copy.insert(server_socket);

    while(running){
        cout << "Server: I am waiting!" << endl;
        fflush(stdout);
        FD_ZERO(&rfds);
        for (auto fd : rfds_copy) {
            FD_SET(fd, &rfds);
        }

        int retval = select(maxfd+1, &rfds, NULL, NULL, NULL);

        if (retval == -1) {
            perror("select:");
            return -1;
        }
        for (fd = server_socket+1; fd <= maxfd; fd++) {
            if (FD_ISSET(fd, &rfds)) {
                n = handle(fd, fds, rfds_copy, maxfd, rfds);
                if (n == -2) {
                    cout << "Server: I am closing!" << endl;
                    running = false;
                    break;
                }
            }
        }
        if (FD_ISSET(server_socket, &rfds)) {
            
            fd = accept(server_socket, (struct sockaddr *) &client_addr, &clen);
            if (fd == -1) {
                perror("accept:");
                return -1;
            }
            // cout << "Server: I got a connection! " << fd << endl;
            n = handle(fd, fds, rfds_copy, maxfd, rfds);
            if (n == -2) {
                cout << "Server: I am closing!" << endl;
                running = false;
                continue;
            }
        }
    }

    for (auto fd : fds) {
        close(fd);
    }

    cout << "Server: I am done!" << endl;
    return 0;
}

int connect_client(string path) {
    int server_socket;
    struct sockaddr_un server_addr;
    int connection_result;

    server_socket = socket(AF_UNIX, SOCK_STREAM, 0);
    if (server_socket == -1) {
        perror("socket:");
        return -1;
    }

    server_addr.sun_family = AF_UNIX;
    server_addr.sun_path[0] = 0;
    strncpy(server_addr.sun_path+1, path.c_str(), path.size());

    // cout << "path: " << path << " " << path.size() << endl;
    int slen = sizeof(server_addr.sun_family) + path.size() + 1;
    connection_result = connect(server_socket, (struct sockaddr *)&server_addr, slen);

    if (connection_result == -1) {
        perror("connect:");
        return -1;
    }
    return server_socket;
}

vector<string> menu = {
    "1. Start a new connection",
    "2. Write a message",
    "3. Read a message",
    "4. Close a connection",
    "5. Batch open",
    "6. Batch write",
    "Else Exit"
};

int client(string path) {
    setvbuf(stdin, NULL, _IOFBF, 16384);
    char * buf = new char[1024];
    int fd;
    vector<int> fds;

    for (unsigned int i = 0; i < menu.size(); i++) {
        cout << menu[i] << endl;
    }
    while (1) {
        cout << "Enter a command:" << endl;
        int n;
        if (scanf("%d", &n) != 1) {
            cout << "Invalid input!" << endl;
            exit(1);
        }
        if (n == 1) {
            fd = connect_client(path);
            cout << "Started a new connection: " << fd << endl;
        } else if (n == 2) {
            // ask for fd and message
            cout << "Enter a message:" << endl;
            read_line(0, buf, 1024);
            cout << "Enter a fd:" << endl;
            if (scanf("%d", &fd) != 1) {
                cout << "Invalid input!" << endl;
                exit(1);
            }

            cout << "I am sending " << buf << " to server! via " << fd << endl;
            write(fd, buf, strlen(buf));
        } else if (n == 3) {
            // ask for fd
            cout << "Enter a fd:" << endl;
            if (scanf("%d", &fd) != 1) {
                cout << "Invalid input!" << endl;
                exit(1);
            }

            read_line(fd, buf, 1024);
            cout << "I received " << buf << " from server!" << endl;
        } else if (n == 4) {
            // ask for fd
            cout << "Enter a fd:" << endl;
            if (scanf("%d", &fd) != 1) {
                cout << "Invalid input!" << endl;
                exit(1);
            }
            close(fd);
        } else if (n == 5) {
            // ask for number of connections
            cout << "Enter the number of connections:" << endl;
            int num;
            if (scanf("%d", &num) != 1) {
                cout << "Invalid input!" << endl;
                exit(1);
            }
            cout << "Enter a message to send to all connections:" << endl;
            read_line(0, buf, 1024);
            fds.clear();
            for (int i = 0; i < num; i++) {
                fd = connect_client(path);
                write(fd, buf, strlen(buf));
                fds.push_back(fd);
            }
            cout << "file descriptors: ";
            for (int i = 0; i < num; i++) {
                cout << fds[i];
                if (i != num-1) {
                    cout << ", ";
                }
            }
            cout << endl;
        } else if (n == 6) {
            // ask for min fd, max fd, message
            cout << "Enter min fd:" << endl;
            int min_fd;
            if (scanf("%d", &min_fd) != 1) {
                cout << "Invalid input!" << endl;
                exit(1);
            }
            cout << "Enter max fd:" << endl;
            int max_fd;
            if (scanf("%d", &max_fd) != 1) {
                cout << "Invalid input!" << endl;
                exit(1);
            }
            cout << "Enter a message to send to all connections:" << endl;
            read_line(0, buf, 1024);
            for (int i = min_fd; i <= max_fd; i++) {
                write(i, buf, strlen(buf));
            }
            cout << "Sent message to all connections!" << endl;
        } else {
            cout << "Exiting!" << endl;
            return 0;
        }
    }
}

int start() {
    int r;
    string path = tmpnam(nullptr);
    struct sockaddr_un server_addr;
    int server_socket = socket(AF_UNIX, SOCK_STREAM, 0);

    server_addr.sun_family = AF_UNIX;
    server_addr.sun_path[0] = 0;
    strncpy(server_addr.sun_path+1, path.c_str(), path.size());

    // cout << "path: " << path << " " << path.size() << server_addr.sun_path << endl;

    int slen = sizeof(server_addr.sun_family) + path.size() + 1;

    r = bind(server_socket, (struct sockaddr *) &server_addr, slen);

    if (r == -1) {
        perror("bind:");
        return -1;
    }

    r = listen(server_socket, 0);
    if (r == -1) {
        perror("listen:");
        return -1;
    }

    int pid = fork();
    if (pid == 0) {
        close(server_socket);
        client(path);
    } else {
        close(0);
        server(server_socket);
    }
    return 0;
}

int main() {
    int r = -1;
    while (r == -1) {
        r = start();
    }
    return 0;
}