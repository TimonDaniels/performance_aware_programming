Performance-Aware Programming
=============================

Course by Casey Muratori at

	https://www.computerenhance.com


Haversine Distance Problem
==========================

**First** generate the test data file by running `gen_test_data.go`.

	cd haversine
	go run gen_test_data.go

This will create `data_10000000_flex.json`. This is necessary for the other
code to run.


The original Python code (listing 21), presented in the course is in
`haversine/haversine_python`.

I rewrote the Python code in Go, not changing it, only adopting it to the
language. See `haversine/haversine_go`.

Finally, I tried my best to create the fastest Go version possible. See
`haversine/haversine_go_fast`

```
Python:
	Result: 10009.199094314288
	Input = 19.12956738471985 seconds
	Math = 18.487126350402832 seconds
	Total = 37.61669373512268 seconds
	Throughput = 265839.418807374 haversines/second

Go:
	Result: 10009.199094314288
	Input = 20.1963482s
	Math = 1.1721565s
	Total = 21.3685047s
	Throughput = 467978.463649822 haversines/second

Optimized Go:
	Result: 10009.199094315622
	Threads = 8
	Count = 10000000
	Total = 518.254ms
	Throughput = 19295558 haversines/second
```

The optimized Go version is 41 times faster than the original Go version and
72.5 times faster than the original Python version.

Note that due to a different order of summation, rounding errors propagate
differently for the optimized version, thus we get a slightly different result.
