//+build ignore

package main

import (
	"fmt"
	"math/rand"
	"os"
	"time"
)

const (
	outputFile = `data_10000000_flex.json`
	count      = 10000000
)

func main() {
	rand.Seed(time.Now().UnixNano())

	f, err := os.Create(outputFile)
	if err != nil {
		panic(err)
	}
	defer f.Close()

	fmt.Fprintln(f, `{"pairs":[`)
	for i := 1; i < count; i++ {
		fmt.Fprint(f, randLine(), ",\n") // Note the comma at the end.
	}
	fmt.Fprint(f, randLine(), "\n") // Last line has no trailing comma.
	fmt.Fprintln(f, `]}`)
}

func randLine() string {
	return fmt.Sprintf(
		`	{"x0":%.6f, "y0":%.6f, "x1":%.6f, "y1":%.6f}`,
		randX(), randY(), randX(), randY(),
	)
}

func randX() float64 {
	return rand.Float64()*360 - 180
}

func randY() float64 {
	return rand.Float64()*180 - 90
}
