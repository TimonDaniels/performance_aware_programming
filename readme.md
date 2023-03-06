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
	Result: 10007.8833106713
	Input = 17.622838020324707 seconds
	Math = 19.40399718284607 seconds
	Total = 37.026835203170776 seconds
	Throughput = 270074.39186008676 haversines/second

Go:
	Result: 10007.8833106713
	Input = 17.8604208s
	Math = 1.1329996s
	Total = 18.9934204s
	Throughput = 526498.1129991731 haversines/second

Optimized Go:
	Result: 10007.88331067118
	Threads = 8
	Count = 10000000
	Total = 377.4745ms
	Throughput = 26491856 haversines/second
```

The optimized Go version is about 50 times faster than the original Go version
and about 100 times faster than the original Python version.

Note that due to a different order of summation, rounding errors propagate
differently for the optimized version, thus we get a slightly different result.
