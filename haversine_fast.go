//+build ignore

package main

import (
	"fmt"
	"math"
	"os"
	"time"
)

const (
	JSONFile      = `data_10000000_flex.json`
	EarthRadiuskm = 6371
)

type pair struct {
	x0, y0, x1, y1 float64
}

func main() {
	start := time.Now()

	data, err := os.ReadFile(JSONFile)
	check(err)

	rawPairs := make(chan rawPair, 100)
	go parseData(data, rawPairs)

	sum := 0.0
	count := 0
	for rawPair := range rawPairs {
		x0 := parseFloat(rawPair.x0)
		y0 := parseFloat(rawPair.y0)
		x1 := parseFloat(rawPair.x1)
		y1 := parseFloat(rawPair.y1)

		sum += haversineOfDegrees(x0, y0, x1, y1, EarthRadiuskm)
		count++
	}
	average := sum / float64(count)
	end := time.Now()

	fmt.Println("Result:", average)
	fmt.Println("Total =", end.Sub(start))
	fmt.Printf("Throughput = %.0f haversines/second\n", float64(count)/(end.Sub(start).Seconds()))
}

type rawPair struct {
	x0, y0, x1, y1 []byte
}

func parseData(data []byte, rawPairs chan rawPair) {
	const (
		findX0 = iota
		parseX0
		findY0
		parseY0
		findX1
		parseX1
		findY1
		parseY1
	)
	state := findX0
	var x0start, x0end, y0start, y0end, x1start, x1end, y1start, y1end int
	pos := 0
	for pos < len(data) {
		c := data[pos]
		switch state {
		case findX0:
			if c == 'x' {
				x0start = pos + 4 // In   "x0":65.477371   skip   x0":
				pos += 11
				state = parseX0
			}
			pos++
		case parseX0:
			if c == ',' || c == '}' {
				x0end = pos
				pos++
				state = findY0
			}
			pos++
		case findY0:
			if c == 'y' {
				y0start = pos + 4
				pos += 11
				state = parseY0
			}
			pos++
		case parseY0:
			if c == ',' || c == '}' {
				y0end = pos
				pos++
				state = findX1
			}
			pos++
		case findX1:
			if c == 'x' {
				x1start = pos + 4
				pos += 11
				state = parseX1
			}
			pos++
		case parseX1:
			if c == ',' || c == '}' {
				x1end = pos
				pos++
				state = findY1
			}
			pos++
		case findY1:
			if c == 'y' {
				y1start = pos + 4
				pos += 11
				state = parseY1
			}
			pos++
		case parseY1:
			if c == ',' || c == '}' {
				y1end = pos
				pos++
				state = findX0

				// Emit pair.
				rawPairs <- rawPair{
					x0: data[x0start:x0end],
					y0: data[y0start:y0end],
					x1: data[x1start:x1end],
					y1: data[y1start:y1end],
				}
			}
			pos++
		}
	}

	close(rawPairs)
}

// parseFloat uses the fact that we know the format of numbers, they all have 6
// decimal digits., e.g.
// 	-116.023599
//
func parseFloat(s []byte) float64 {
	// Parse sign.
	sign := 1.0
	if s[0] == '-' {
		sign = -1.0
		s = s[1:]
	}

	// Parse decimal part at the end.
	n := len(s)
	decimal := 0.0 +
		0.1*float64(s[n-6]-'0') +
		0.01*float64(s[n-5]-'0') +
		0.001*float64(s[n-4]-'0') +
		0.0001*float64(s[n-3]-'0') +
		0.00001*float64(s[n-2]-'0') +
		0.000001*float64(s[n-1]-'0')

	// Parse integer part at the start.
	integer := 0.0
	scale := 1.0
	for i := n - 8; i >= 0; i-- {
		integer += scale * float64(s[i]-'0')
		scale *= 10
	}

	return sign * (integer + decimal)
}

func haversineOfDegrees(X0, Y0, X1, Y1, R float64) float64 {
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

func check(err error) {
	if err != nil {
		panic(err)
	}
}
