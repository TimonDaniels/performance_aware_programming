Performance Oriented Programming
================================


Course by Casey Muratori at

	https://www.computerenhance.com/


First baseline measurements with Python from the original listing 21:

# Run 1
	Result: 10009.199094314288
	Input = 17.723998546600342 seconds
	Math = 18.187000513076782 seconds
	Total = 35.910999059677124 seconds
	Throughput = 278466 haversines/second

# Run 2
	Result: 10009.199094314288
	Input = 18.552680492401123 seconds
	Math = 17.66699719429016 seconds
	Total = 36.219677686691284 seconds
	Throughput = 276093 haversines/second

So roughly:
	Throughput = 277000 haversines/second


Now a baseline with the same code translated to Go:

	Result: 10009.199094314288
	Input = 19.1525366s
	Math = 1.1659993s
	Total = 20.3185359s
	Throughput = 492161 haversines/second

	Result: 10009.199094314288
	Input = 19.529693s
	Math = 1.1883386s
	Total = 20.7180316s
	Throughput = 482671 haversines/second

So roughly:
	Throughput = 487000 haversines/second


The first hand-rolled Go version with custom JSON parsing:

	Result: 10009.199094314288
	Total = 3.6980314s
	Throughput = 2704141 haversines/second
