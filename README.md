# GigaParserCC

1. [Notice](#notice)
2. [Etymology](#etymology)
3. [Technical Info](#technical-info)
3. [TODOs](#todos)


## Notice
Code quality was never a project goal, as this code was an internal project, e.g. **in house**;  
Having said that, feel free to offer PR for code quality.

## Etymology
Giga - Since each file is around 1 GB (see disclaimer)  
Parser - Since we're parsing data from websites  
CC - Since we're working with CommonCrawl files  

## Project Description
This project:
 - parse websites for signatures, e.g.
 - run Regexes on content of HTML pages, e.g.
 - extract emails / technologies used / other information from HTML pages, e.g.
 - use CommonCrawl data to search patterns in HTML pages fast (1)

### Sample scrapers 
* technologies used
See attached file, cc_downloader_tech.py, to see how to extract tech stack


## Technical Info
### Regex libs
Several regex libs were tested:
- Old plain "re" python module - nice for some use cases
- re2 (https://github.com/google/re2 && https://github.com/facebook/pyre2)
- hyperscan (https://github.com/intel/hyperscan)
- regex + trie preprocesses (https://stackoverflow.com/a/42789508 or https://github.com/G-Research/fast-string-search) - looks promising but wasn't tested
  
hyperscan is a clearcut winner when it comes to multiple (~500) regex searches at once.  
In addition, it's easier to scan multiple regex concurrently using hyperscan - it can be done using hyperscan API.  
With re/re2, however, you'd have to concat all regular expressions into 1 single expression using |, e.g. something like:
```
regex_list = ["fi.st_regex", "second_?reg.x", ...]
regex_str = "(" + |".join([remove_capture_group(s) for s in regex_list]) + ")"
united_regex = re.compile(regex_from_file)
```




### Queue system
We used multiprocessing.Queue for IPC between producer process and consumer processes.  
We use several optimizations, e.g. batching 


However, we could use RabbitMQ or other similar queueing system to get some free
e.g., in this design document, http://aosabook.org/en/zeromq.html, we could see some of zeromq internals:
pre-read, pre-write buffers.

### S3
2 options to parse the CommonCrawl corpus:
Parallel, or using random seek.  
It's clear to every software developer that sequential read if faster than random seek [see https://bit.ly/33O3fBY+].  
However, we realized that parsing 60K files (60 TB) will take us too much time and money.

So, a pre-processing phase over Athena is done.  
Using Regex, we output only specific URLs, e.g. urls of next format:
```
www.domain.com/
www.domain.com/about-us/
www.domain.com/about-us.html
www.domain.com/about-us.php
```

In addition, and since the files are public, we could use http/https/boto3.  
Found that HTTP works the best (faster than HTTP*s* and boto3).


### Process Count Tuning
We have 2 bottlenecks in here:
* Network latency - Latencies for getting chunks (about 100k each) from S3
* CPU - Regex processing

For the network latency issue, we are not bounded to the number of cores. So we use around 500 processes.  
For the CPU, we are indeed bounded to the number of cores; however, we don't pay high price for having 500 processes (context-switch wise).


## TODOs:
* Build time is too high
* Finish docker-izing environment


