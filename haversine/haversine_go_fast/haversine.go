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
	check(err)
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
// Each part starts at a pair, the first part always starts at 0, the others
// start at "x0".The last item in the returned array is always len(data). For
// example, splitting 100 bytes into 4 parts results in:
//
// 	[0, 25, 50, 75, 100]
//
// creating four intervals: [0,25], [25,50], [50,75], [75,100].
func splitAtPairBoundaries(data []byte, parts int) []int {
	splits := []int{0} // First marker is always at 0.

	for i := 1; i < parts; i++ {
		start := i * len(data) / parts
		for data[start] != '\n' {
			start++
		}
		splits = append(splits, start+3)
	}

	splits = append(splits, len(data)) // Last marker is always at the end.

	return splits
}

func haversineAverage(data []byte) (sum float64, count int) {
	// The data looks like this:
	//
	// {"pairs":[
	// 	{"x0":37.677704, "y0":79.291636, "x1":59.241619, "y1":-11.211446},
	// 	{"x0":-27.130501, "y0":33.628153, "x1":-156.370673, "y1":-61.826534},
	// 	...
	// 	{"x0":53.442258, "y0":85.797202, "x1":155.772353, "y1":-36.418042},
	// 	{"x0":-98.188135, "y0":8.463621, "x1":-58.979798, "y1":85.554110}
	// ]}
	//
	// and in this function we are given a part of that, either:
	//
	// {"pairs":[
	// 	{"x0":37.677704, "y0":79.291636, "x1":59.241619, "y1":-11.211446},
	// 	{"x0":-27.130501, "y0":33.628153, "x1":-156.370673, "y1":-61.826534},
	// 	{
	//
	// at the start, or:
	//
	// "x0":37.677704, "y0":79.291636, "x1":59.241619, "y1":-11.211446},
	// 	{"x0":-27.130501, "y0":33.628153, "x1":-156.370673, "y1":-61.826534},
	// 	{
	//
	// for middle parts, or:
	//
	// "x0":53.442258, "y0":85.797202, "x1":155.772353, "y1":-36.418042},
	// 	{"x0":-98.188135, "y0":8.463621, "x1":-58.979798, "y1":85.554110}
	// ]}
	//
	// at the end. See splitAtPairBoundaries for how these are split.

	pos := 0

	// Set pos to the first '"' at the start of "x0":... by finding 'x' and then
	// stepping back by one.
	for data[pos] != 'x' {
		pos++
	}
	pos--

	totalEnd := len(data) - 8
	for pos < totalEnd {
		// Our pos is at the quotes in "x0":... and we keep it there in each
		// iteration.
		//
		// The number can have these forms:
		//
		// 	"x0":1.123456, ...
		// 	"x0":12.123456, ...
		// 	"x0":123.123456, ...
		// 	"x0":-123.123456, ...
		// 	_^^^^^ <- skip 5 bytes from the '"' to get the number start.
		//
		// meaning we have 8, 9, 10 or 11 bytes in each number.

		x0start := pos + 5
		x0end := x0start + 8 // Assume 8 byte number.
		if data[x0end+1] == ',' {
			x0end++ // This is a 9 byte number.
		} else if data[x0end+2] == ',' {
			x0end += 2 // This is a 10 byte number.
		} else if data[x0end+3] == ',' {
			x0end += 3 // This is a 11 byte number.
		}

		// {"x0":53.442258, "y0":85.797202, ...
		y0start := x0end + 7
		y0end := y0start + 8
		if data[y0end+1] == ',' {
			y0end++
		} else if data[y0end+2] == ',' {
			y0end += 2
		} else if data[y0end+3] == ',' {
			y0end += 3
		}

		// ... "y0":85.797202, "x1":155.772353, ...
		x1start := y0end + 7
		x1end := x1start + 8
		if data[x1end+1] == ',' {
			x1end++
		} else if data[x1end+2] == ',' {
			x1end += 2
		} else if data[x1end+3] == ',' {
			x1end += 3
		}

		// ... "x1":155.772353, "y1":-36.418042},
		y1start := x1end + 7
		y1end := y1start + 8
		if data[y1end+1] == '}' {
			y1end++
		} else if data[y1end+2] == '}' {
			y1end += 2
		} else if data[y1end+3] == '}' {
			y1end += 3
		}

		pos = y1end + 5

		// We have a complete pair. Parse it and calculate its distance.

		x0 := parseFloat(data[x0start:x0end])
		y0 := parseFloat(data[y0start:y0end])
		x1 := parseFloat(data[x1start:x1end])
		y1 := parseFloat(data[y1start:y1end])

		const EarthRadiuskm = 6371
		sum += haversineOfDegrees(x0, y0, x1, y1, EarthRadiuskm)
		count++
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
