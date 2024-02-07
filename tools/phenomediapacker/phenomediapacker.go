package main

import (
	"encoding/binary"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

type FileEntry struct {
	Filename string
	Filesize int64
}

func encryptConfig(data []byte) {
	key := uint(0x1234)
	for i := range data {
		uVar2 := data[i] & 0x55
		cVar1 := data[i] & 0xAA
		cVar1 >>= 1
		uVar2 <<= 1
		data[i] = (uVar2 ^ cVar1) ^ byte(key&0xFF)
		key = key*3 + 2 & 0xffff
	}
}

func generateHeader(name string, numFiles uint32) []byte {
	header := make([]byte, 0x40)
	copy(header, name)
	binary.LittleEndian.PutUint32(header[0x20:], numFiles)
	binary.LittleEndian.PutUint32(header[0x24:], 0x100)
	return header
}

func main() {
	var inputFolder, outputPath string
	flag.StringVar(&inputFolder, "input", "", "Path to the input folder containing data files")
	flag.StringVar(&outputPath, "output", "packed.dat", "Output path for the resulting .dat file")
	flag.Parse()

	if inputFolder == "" {
		fmt.Println("Input folder is required")
		flag.Usage()
		os.Exit(1)
	}

	var files []FileEntry
	err := filepath.Walk(inputFolder, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}

		if !info.IsDir() {
			files = append(files, FileEntry{Filename: path, Filesize: info.Size()})
		}
		return nil
	})
	if err != nil {
		fmt.Printf("Error walking through input folder: %s\n", err)
		return
	}

	outFile, err := os.Create(outputPath)
	if err != nil {
		fmt.Printf("Error creating output file: %s\n", err)
		return
	}
	defer outFile.Close()

	header := generateHeader("Moorhuhn", uint32(len(files)))
	outFile.Write(header)

	offset := int64(0x40 + len(files)*0x80)
	for _, file := range files {
		fileEntry := make([]byte, 0x80)
		relativePath, _ := filepath.Rel(inputFolder, file.Filename)
		copy(fileEntry, "data\\" + strings.ReplaceAll(relativePath, "/", "\\"))

		binary.LittleEndian.PutUint64(fileEntry[0x68:], uint64(offset))
		binary.LittleEndian.PutUint64(fileEntry[0x6C:], uint64(file.Filesize))
		offset += file.Filesize + (file.Filesize % 0x100)
		outFile.Write(fileEntry)
	}

	for _, file := range files {
		data, err := os.ReadFile(file.Filename)
		if err != nil {
			fmt.Printf("Error reading file %s: %s\n", file.Filename, err)
			continue
		}
		if filepath.Ext(file.Filename) == ".txt" {
			encryptConfig(data)
		}
		padding := make([]byte, file.Filesize%0x100)
		outFile.Write(append(data, padding...))
	}

	fmt.Println("Packing completed successfully.")
}
