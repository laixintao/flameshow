package main

import (
	"encoding/json"
	"unsafe"

	"github.com/google/pprof/profile"
)

// #include <stdio.h>
// #include <stdlib.h>
import "C"

func ProfileToJson(profileData []byte) (string, error) {
	prof, err := profile.ParseData(profileData)

	if err != nil {
		return "", err
	}

	jsonFormat, err := toFullJSON(prof)

	if err != nil {
		return "", err
	}

	return string(jsonFormat), nil
}

func toFullJSON(prof *profile.Profile) ([]byte, error) {
	jsonFormat, err := json.Marshal(prof)
	if err != nil {
		return []byte{}, err
	}
	return jsonFormat, nil
}

//export ParseProfile
func ParseProfile(profile *C.char, length C.int) (*C.char, *C.char) {

	slice := C.GoBytes(unsafe.Pointer(profile), length)

	jsonStr, err := ProfileToJson(slice)

	if err != nil {
		return C.CString("{}"), C.CString(err.Error())
	}

	return C.CString(jsonStr), C.CString("")
}

//export FreeString
func FreeString(str *C.char) {
	C.free(unsafe.Pointer(str))
}

func main() {}
