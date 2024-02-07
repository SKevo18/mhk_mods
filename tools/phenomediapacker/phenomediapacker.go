package main

import (
	"encoding/binary"
	"fmt"
	"os"
	"path/filepath"
	"strings"
)

type FileEntry struct {
	Filename string
	FileSize uint32
}

func encryptConfig(data []byte) {
	key := uint32(0x1234)
	for i := range data {
		uVar2 := data[i] & 0x55
		cVar1 := data[i] & 0xAA
		cVar1 >>= 1
		uVar2 <<= 1
		data[i] = (uVar2 ^ cVar1) ^ byte(key&0xFF)
		key = (key*3 + 2) & 0xffff
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
	fmt.Println("Phenomedia packer by pyramidensurfer")

	if len(os.Args) < 3 {
		fmt.Println("Usage: phenomediapacker <input path> <output path>")
		os.Exit(1)
	}

	inputPath := os.Args[1]
	outputPath := os.Args[2]

	if _, err := os.Stat(inputPath); os.IsNotExist(err) {
		fmt.Printf("Input path %s does not exist\n", inputPath)
		os.Exit(1)
	}

	var files []FileEntry
	filepath.Walk(inputPath, func(path string, info os.FileInfo, err error) error {
		if err != nil {
			fmt.Printf("Error accessing path %q: %v\n", path, err)
			os.Exit(1)
		}
		if !info.IsDir() {
			files = append(files, FileEntry{Filename: path, FileSize: uint32(info.Size())})
		}
		return nil
	})

	gameID := "Moorhuhn"
	outFileName := outputPath
	if len(os.Args) > 1 {
		inputFile, err := os.Open(os.Args[1])
		if err == nil {
			defer inputFile.Close()
			var oheadername [0x20]byte
			inputFile.Read(oheadername[:])
			gameID = string(oheadername[:])
		} else {
			fmt.Printf("Error opening %s\n", os.Args[1])
			outFileName = outputPath
			gameID = "Moorhuhn"
		}
	}

	fmt.Printf("Packing for %s\n", gameID)

	outfile, err := os.Create(outFileName)
	if err != nil {
		fmt.Printf("Error creating output file: %v\n", err)
		return
	}
	defer outfile.Close()

	header := generateHeader(gameID, uint32(len(files)))
	outfile.Write(header)

	offset := uint32(0x40 + len(files)*0x80)

	for _, f := range files {
		fileEntry := make([]byte, 0x80)
		copy(fileEntry, f.Filename)
		binary.LittleEndian.PutUint32(fileEntry[0x68:], offset)
		binary.LittleEndian.PutUint32(fileEntry[0x6C:], f.FileSize)
		offset += f.FileSize + (f.FileSize % 0x100)
		outfile.Write(fileEntry)
	}

	for _, f := range files {
		fileData, err := os.ReadFile(f.Filename)
		if err != nil {
			fmt.Printf("Error reading file %s: %v\n", f.Filename, err)
			continue
		}

		fmt.Printf("Packing %s\n", f.Filename)
		if strings.HasSuffix(f.Filename, ".txt") {
			encryptConfig(fileData)
		}
		padding := make([]byte, f.FileSize%0x100)
		outfile.Write(append(fileData, padding...))
	}
}
