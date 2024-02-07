# MHK 2 Packer

This tool is used to pack data file for MHK 2, including configuration files (QuickBMS script can't properly encode `.txt` configs).

## Build

```bash
go build -o build/
```

## Credit

The original C++ source for this tool was provided by pyramidensurfer:

```cpp
#include <filesystem>
#include <iostream>
#include <list>
#include <fstream>

void encrypt_config(char* data, int data_size)

{
    char cVar1;
    unsigned int uVar2;
    unsigned int key;
    int index;

    index = 0;
    key = 0x1234;
    if (0 < data_size) {
        do {
            uVar2 = *(char*)(index + data) & 0x55;
            cVar1 = *(char*)(index + data) & 0xAA;
            cVar1 >>= 1;
            uVar2 <<= 1;
            *(char*)(index + data) = (uVar2 ^ cVar1) ^ (key & 0xFF);
            key = key * 3 + 2 & 0xffff;
            index = index + 1;
        } while (index < data_size);
    }
    return;
}

struct file_entry{
    std::string filename;
    unsigned int filesize;
} ;

std::string generate_header(std::string name, unsigned int num_files) {
    char header[0x40];
    memset(header, 0, 0x40);
    memcpy(header, name.c_str(), name.size());
    *((unsigned int*)(&header[0x20])) = num_files;
    *((unsigned int*)(&header[0x24])) = 0x100;
    return std::string(header, 0x40);
}

int main(int argc, char* argv[]) {
    std::cout << "Phenomedia packer by pyramidensurfer" << std::endl;
    std::list<file_entry> files;
    std::string game_id, out_file_name;
    for (const auto& dirEntry : std::filesystem::recursive_directory_iterator("data")) {
        if (dirEntry.is_regular_file()) {
            ile_entry f;
            f.filename = dirEntry.path().string();
            f.filesize = dirEntry.file_size();
            files.push_back(f);
        }
    }


    if (argc > 1) {
        std::ifstream odat(argv[1], std::ios::in | std::ios::binary);
        if (odat.is_open()) {
            char oheadername[0x20];
            odat.read(oheadername, 0x20);
            odat.close();
            game_id.append(oheadername);
            std::string newfilename(argv[1]);
            newfilename.append(".original");
            out_file_name = argv[1];
            if (std::rename(argv[1], newfilename.c_str())) out_file_name.append(".repacked");
        }
        else {
            std::cout << "Error opening " << argv[1] << std::endl;
            out_file_name = "packed.dat";
            game_id = "Moorhuhn";
        }
    }
    else {
        out_file_name = "packed.dat";
        game_id = "Moorhuhn";
    }

    std::cout << "Packing for " << game_id << std::endl;

    std::ofstream outfile(out_file_name, std::ios::out | std::ios::binary);    

    outfile << generate_header(game_id, files.size());
    
    unsigned int offset = 0x40 + files.size() * 0x80;    

    for (auto const& i : files) {
        char file_entry[0x80];
        memset(file_entry, 0, 0x80);
        memcpy(file_entry, i.filename.c_str(), i.filename.size());
        *((unsigned int*)(&file_entry[0x68])) = offset;
        *((unsigned int*)(&file_entry[0x6C])) = i.filesize;
        offset += i.filesize + (i.filesize % 0x100);
        outfile.write(file_entry, 0x80);
    }

    for (auto const& i : files) {
        std::ifstream infile(i.filename, std::ios::in | std::ios::binary);
        std::string file_data;        
        if (infile.is_open()) {
            std::cout << "Packing " << i.filename << std::endl;
            char* buffer = new char[i.filesize + (i.filesize % 0x100)];
            infile.read(buffer, i.filesize);
            if (i.filename.find(".txt") != std::string::npos) encrypt_config(buffer, i.filesize);
            outfile.write(buffer, (i.filesize + (i.filesize % 0x100)));
            delete[] buffer;
            infile.close();
        }
        else std::cout << "Error opening file " << i.filename << ". " << std::endl;
    }
    files.clear();
    outfile.close();

    system("pause");
}
```

Conversion to Go was performed by me.
