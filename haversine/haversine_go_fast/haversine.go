package main

import (
	"fmt"
	"math"
	"os"
	"sync"
	"time"

	"github.com/edsrzf/mmap-go"
)

const (
	JSONFile = `../data_10000000_flex.json`
	threads  = 8 // Number of Go routines working on the input.
)

func main() {
	start := time.Now()

	// Memory-map the file.

	inputFile, err := os.OpenFile(JSONFile, os.O_RDWR, 0644)
	// TODO Why is this so costly? Look at the generated code. Checking this
	// error seems to decrease performance by 3 to 4 % for some reason.
	//check(err)
	defer inputFile.Close()

	// data holds the contents of the file as a []byte.
	data, err := mmap.Map(inputFile, mmap.RDWR, 0)
	check(err)
	defer data.Unmap()

	// Split the data into equal parts and compute each part's average
	// concurrently.

	splits := splitAtPairBoundaries(data, threads)

	var (
		sums   [threads]float64
		counts [threads]int
		wg     sync.WaitGroup
	)
	wg.Add(threads)
	for i := 0; i < threads; i++ {
		go func(i int) {
			a, b := splits[i], splits[i+1]
			dataPart := data[a:b]
			sums[i], counts[i] = haversineAverage(dataPart)
			wg.Done()
		}(i)
	}
	wg.Wait()

	// Combine the results into one average.

	sum := 0.0
	count := 0
	for i := 0; i < threads; i++ {
		sum += sums[i]
		count += counts[i]
	}
	average := sum / float64(count)

	end := time.Now()

	fmt.Println("Result:", average)
	fmt.Println("Threads =", threads)
	fmt.Println("Count =", count)
	fmt.Println("Total =", end.Sub(start))
	fmt.Printf("Throughput = %.0f haversines/second\n", float64(count)/(end.Sub(start).Seconds()))
}

// splitAtPairBoundaries returns the indices at which to split data into parts.
// Splits are moved to the next line break in order not to split in the middle
// of a pair. We want to split at "x0" data in the JSON file.
// The returned indices start at 0 and end at len(data).
// For example, splitting 100 bytes into 4 parts results in:
//
// 	[0, 25, 50, 75, 100]
//
// meaning four intervals: [0,25], [25,50], [50,75], [75,100].
func splitAtPairBoundaries(data []byte, parts int) []int {
	splits := []int{0} // First marker is always at 0.

	for i := 1; i < parts; i++ {
		start := i * len(data) / parts
		for data[start] != '\n' {
			start++
		}
		splits = append(splits, start)
	}

	splits = append(splits, len(data)) // Last marker is always at the end.

	return splits
}

func haversineAverage(data []byte) (sum float64, count int) {
	// These are the states we iterate through. We know the order of the values
	// in the file: x0, y0, x1, y1 for each line.
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
			if c == '"' {
				// When we point to the first quotes in
				//
				// 	"x0":65.477371, ...
				// 	^
				// we know that the start of the number is 5 right of the '"'.
				x0start = pos + 5

				// The shortest possible number string has exactly one digit
				// before the decimal point, like this:
				//
				//	 "x0":0.123456, ...
				// 	 ^^^^^^^^^^^^^     <- Skip these 13 characters.
				//
				// We are at the '"' so know that we can always at least skip 13
				// characters to find the comma after the number.
				// If the number is longer, fine, we will keep looking for the
				// comma in the parse state.
				// We skip 12 here in the if and 1 after the if,
				// unconditionally.
				pos += 12
				state = parseX0
			}
			pos++
		case parseX0:
			if c == ',' || c == '}' {
				x0end = pos
				// We can skip an extra character, since a comma is followed by
				// a space and a closing brace is followed by a comma or line
				// break.
				pos++
				state = findY0
			}
			pos++
		case findY0:
			if c == '"' {
				y0start = pos + 5
				pos += 12
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
			if c == '"' {
				x1start = pos + 5
				pos += 12
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
			if c == '"' {
				y1start = pos + 5
				pos += 12
				state = parseY1
			}
			pos++
		case parseY1:
			if c == ',' || c == '}' {
				y1end = pos
				pos++
				state = findX0 // Go back to the start, parse the next pair.

				// We have a complete pair. Parse it and calculate its distance.

				x0 := parseFloat(data[x0start:x0end])
				y0 := parseFloat(data[y0start:y0end])
				x1 := parseFloat(data[x1start:x1end])
				y1 := parseFloat(data[y1start:y1end])

				const EarthRadiuskm = 6371
				sum += haversineOfDegrees(x0, y0, x1, y1, EarthRadiuskm)
				count++
			}
			pos++
		}
	}

	return
}

// parseFloat uses the fact that we know the format of numbers, they all have 6
// decimal digits., e.g.
//
// 	   8.347589
// 	  55.237895
// 	-116.023599
func parseFloat(s []byte) float64 {
	// Parse sign.
	sign := 1.0
	if s[0] == '-' {
		sign = -1.0
		s = s[1:] // Remove sign.
	}

	n := len(s)

	if n == 8 {
		// Index: n-87654321
		// Digit:   x.xxxxxx
		unscaled := -1111111*'0' +
			int(s[n-8])*1000000 +
			int(s[n-6])*100000 +
			int(s[n-5])*10000 +
			int(s[n-4])*1000 +
			int(s[n-3])*100 +
			int(s[n-2])*10 +
			int(s[n-1])
		return sign * 0.000001 * float64(unscaled)
	} else if n == 9 {
		// Index: n-987654321
		// Digit:   xx.xxxxxx
		unscaled := -11111111*'0' +
			int(s[n-9])*10000000 +
			int(s[n-8])*1000000 +
			int(s[n-6])*100000 +
			int(s[n-5])*10000 +
			int(s[n-4])*1000 +
			int(s[n-3])*100 +
			int(s[n-2])*10 +
			int(s[n-1])
		return sign * 0.000001 * float64(unscaled)
	} else {
		// Index: n-10987654321
		// Digit:    xxx.xxxxxx
		unscaled := -111111111*'0' +
			int(s[n-10])*100000000 +
			int(s[n-9])*10000000 +
			int(s[n-8])*1000000 +
			int(s[n-6])*100000 +
			int(s[n-5])*10000 +
			int(s[n-4])*1000 +
			int(s[n-3])*100 +
			int(s[n-2])*10 +
			int(s[n-1])
		return sign * 0.000001 * float64(unscaled)
	}
}

// haversineOfDegrees computes the distance as in the original Python code.
func haversineOfDegrees(x0, y0, x1, y1, radius float64) float64 {
	radians := func(degrees float64) float64 {
		const degToRad = math.Pi / 180.0
		return degrees * degToRad
	}

	square := func(x float64) float64 {
		return x * x
	}

	sin := math.Sin
	cos := math.Cos
	asin := math.Asin
	sqrt := math.Sqrt

	dY := radians(y1 - y0)
	dX := radians(x1 - x0)
	y0 = radians(y0)
	y1 = radians(y1)

	rootTerm := square(sin(dY/2)) + cos(y0)*cos(y1)*(square(sin(dX/2)))
	result := 2 * radius * asin(sqrt(rootTerm))

	return result
}

func check(err error) {
	if err != nil {
		panic(err)
	}
}
