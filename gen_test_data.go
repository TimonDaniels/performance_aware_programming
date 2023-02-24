//+build ignore

package main

import (
	"fmt"
	"math/rand"
	"time"
)

const count = 10000000

func main() {
	rand.Seed(time.Now().UnixNano())

	fmt.Println(`{"pairs":[`)
	for i := 1; i < count; i++ {
		fmt.Print(randLine(), ",\n")
	}
	fmt.Print(randLine(), "\n") // Last line has no trailing comma.
	fmt.Println(`]}`)
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
