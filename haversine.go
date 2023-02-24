//+build ignore

package main

import (
	"encoding/json"
	"fmt"
	"math"
	"os"
	"time"
)

const JSONFile = `data_10000000_flex.json`

type Input struct {
	Pairs []Pair `json:"pairs"`
}

type Pair struct {
	X0 float64 `json:"x0"`
	Y0 float64 `json:"y0"`
	X1 float64 `json:"x1"`
	Y1 float64 `json:"y1"`
}

func main() {
	// Read the input

	jsonFile, err := os.Open(JSONFile)
	check(err)
	defer jsonFile.Close()

	StartTime := time.Now()
	var JSONInput Input
	check(json.NewDecoder(jsonFile).Decode(&JSONInput))
	MidTime := time.Now()

	// Average the haversines

	HaversineOfDegrees := func(X0, Y0, X1, Y1, R float64) float64 {
		const degToRad = math.Pi / 180.0
		radians := func(degrees float64) float64 {
			return degrees * degToRad
		}

		square := func(x float64) float64 {
			return x * x
		}

		dY := radians(Y1 - Y0)
		dX := radians(X1 - X0)
		Y0 = radians(Y0)
		Y1 = radians(Y1)

		RootTerm := (square(math.Sin(dY / 2))) + math.Cos(Y0)*math.Cos(Y1)*(square(math.Sin(dX/2)))
		Result := 2 * R * math.Asin(math.Sqrt(RootTerm))

		return Result
	}

	const EarthRadiuskm = 6371
	Sum := 0.0
	Count := 0
	for _, Pair := range JSONInput.Pairs {
		Sum += HaversineOfDegrees(Pair.X0, Pair.Y0, Pair.X1, Pair.Y1, EarthRadiuskm)
		Count++
	}
	Average := Sum / float64(Count)
	EndTime := time.Now()

	// Display the result

	fmt.Println("Result:", Average)
	fmt.Println("Input =", MidTime.Sub(StartTime))
	fmt.Println("Math =", EndTime.Sub(MidTime))
	fmt.Println("Total =", EndTime.Sub(StartTime))
	fmt.Println("Throughput =", float64(Count)/(EndTime.Sub(StartTime).Seconds()), "haversines/second")
}

func check(err error) {
	if err != nil {
		panic(err)
	}
}
