import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup
import lxml
import requests
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from utils import get_logger

VALID_URLS = {'ics.uci.edu', '.cs.uci.edu', '.informatics.uci.edu', '.stat.uci.edu', 'today.uci.edu'}

WEBSITE_STOPWORDS = """a
about
above
after
again
against
all
am
an
and
any
are
aren't
as
at
be
because
been
before
being
below
between
both
but
by
can't
cannot
could
couldn't
did
didn't
do
does
doesn't
doing
don't
down
during
each
few
for
from
further
had
hadn't
has
hasn't
have
haven't
having
he
he'd
he'll
he's
her
here
here's
hers
herself
him
himself
his
how
how's
i
i'd
i'll
i'm
i've
if
in
into
is
isn't
it
it's
its
itself
let's
me
more
most
mustn't
my
myself
no
nor
not
of
off
on
once
only
or
other
ought
our
ours	
ourselves
out
over
own
same
shan't
she
she'd
she'll
she's
should
shouldn't
so
some
such
than
that
that's
the
their
theirs
them
themselves
then
there
there's
these
they
they'd
they'll
they're
they've
this
those
through
to
too
under
until
up
very
was
wasn't
we
we'd
we'll
we're
we've
were
weren't
what
what's
when
when's
where
where's
which
while
who
who's
whom
why
why's
with
won't
would
wouldn't
you
you'd
you'll
you're
you've
your
yours
yourself
yourselves
"""




def tokenize(textfilepath: str) -> [str]:
    
    set_of_words = set(WEBSITE_STOPWORDS.split(' '))

    stop_words = set(stopwords.words('english'))


    tokenList = []
    
    file = open(textfilepath, "r")
        for line in file:
            line = line.rstrip()
            line = line.lstrip()
            wordList = line.split()        
            try:

                word_tokens = word_tokenize(wordList)

            except:
                continue
    
    

    for w in word_tokens:
        if w not in stop_words:
            tokenList.append(w)
            
    return tokenList

#runtime of this function is O(N) as the function goes through all elements
def computeWordFrequencies(tokenList: [str]) -> dict:

    tokenMap = {}

    for word in tokenList:
        if word not in tokenMap:
            tokenMap[word] = 1
        else:
            tokenMap[word] = tokenMap[word] + 1


    return tokenMap

#runtime of this function is O(Nlogn) as the function uses the sort function
def printa(tokenMap: dict) -> None:

    tokenbyvalue = sorted(tokenMap.items(), key=lambda item: item[1], reverse=True)
    for key in tokenbyvalue:
        print(key[0], key[1])


def scraper(url, resp):
    links = extract_next_links(url, resp)
    return [link for link in links if is_valid(link)]

def extract_next_links(url, resp):
    next_link = []
    try:
        soup = BeautifulSoup(resp.raw_response.content, 'html.parser')
        for link in soup.findAll('a'):
            try:
                next_link.append(link['href'])
    
            # href attribute does not exist in <a> tag.
            except KeyError:
                print("Status Code:", resp.status, "\nError Message: href attribute does not exist.")
    
    # Checks for restricted page.
    except AttributeError:
        print("Status Code:", resp.status, "\nError Message:", resp.error)

    return next_link

def is_valid(url):
    try:
        parsed = urlparse(url)
        if parsed.scheme not in set(["http", "https"]):
            return False

        valid_domain = False

        # Check Domain : url needs to be in the Valid url set
        for domain in VALID_URLS:
            if domain in parsed.netloc:
                if parsed.netloc == 'today.uci.edu' and parsed.path[:41] == '/department/information_computer_sciences':
                    valid_domain = True
                else:
                    valid_domain = True

        if valid_domain == False:
            return False

        return not re.match(
            r".*\.(css|js|bmp|gif|jpe?g|ico"
            + r"|png|tiff?|mid|mp2|mp3|mp4"
            + r"|wav|avi|mov|mpeg|ram|m4v|mkv|ogg|ogv|pdf"
            + r"|ps|eps|tex|ppt|pptx|doc|docx|xls|xlsx|names"
            + r"|data|dat|exe|bz2|tar|msi|bin|7z|psd|dmg|iso"
            + r"|epub|dll|cnf|tgz|sha1"
            + r"|thmx|mso|arff|rtf|jar|csv"
            + r"|rm|smil|wmv|swf|wma|zip|rar|gz)$", parsed.path.lower())

    except TypeError:
        print ("TypeError for ", parsed)
        raise
