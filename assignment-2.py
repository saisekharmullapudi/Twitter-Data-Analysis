import twitter
import json
import sys
import time
from urllib.error import URLError
from http.client import BadStatusLine
from functools import partial
from sys import maxsize as maxint
import operator
from heapq import nlargest
import networkx as nx
import matplotlib.pyplot as plt
##### checking -changing 
###### git push code -- working
### commit -1

##############Divya Sai Sekhar Mullapudi##########################
########################################
CONSUMER_KEY = 'jSGpY3OvBrMfCgfPBARQsEL7C'
CONSUMER_SECRET = 'AxPsW6XdjCH3BAVFb0lcCtIFpHlPDyarExC8vOKIqu6bhf0YnA'
OAUTH_TOKEN = '1535994133-CzSEffHsa8xG66NMNWaU9msp72gbHOlBdLFZO9y'
OAUTH_TOKEN_SECRET = 'dSkfjRBEwc4wefoWmADWG5DHchJIyZP8G9a11QCRUJHP8'
starting_point="MDSSEKHAR"
#MDSSEKHAR #KingJames #kobebryant
########################################
########################################
############ ---many thing to know more
#########3## branch to be merged

auth = twitter.oauth.OAuth(OAUTH_TOKEN, OAUTH_TOKEN_SECRET,CONSUMER_KEY, CONSUMER_SECRET)
twitter_api = twitter.Twitter(auth=auth)

###########
# code from Twitter Code Book to get make a twitter request to resolve the number of limited API requests to resolve;
def make_twitter_request(twitter_api_func, max_errors=10, *args, **kw):
    # A nested helper function that handles common HTTPErrors. Return an updated
    # value for wait_period if the problem is a 500 level error. Block until the
    # rate limit is reset if it's a rate limiting issue (429 error). Returns None
    # for 401 and 404 errors, which requires special handling by the caller.
    def handle_twitter_http_error(e, wait_period=2, sleep_when_rate_limited=True):

        if wait_period > 3600:  # Seconds
            print('Too many retries. Quitting.', file=sys.stderr)
            raise e

        # See https://developer.twitter.com/en/docs/basics/response-codes
        # for common codes

        if e.e.code == 401:
            print('Encountered 401 Error (Not Authorized)', file=sys.stderr)
            return None
        elif e.e.code == 404:
            print('Encountered 404 Error (Not Found)', file=sys.stderr)
            return None
        elif e.e.code == 429:
            print('Encountered 429 Error (Rate Limit Exceeded)', file=sys.stderr)
            if sleep_when_rate_limited:
                print("Retrying in 15 minutes...ZzZ...", file=sys.stderr)
                sys.stderr.flush()
                time.sleep(60 * 15 + 5)
                print('...ZzZ...Awake now and trying again.', file=sys.stderr)
                return 2
            else:
                raise e  # Caller must handle the rate limiting issue
        elif e.e.code in (500, 502, 503, 504):
            print('Encountered {0} Error. Retrying in {1} seconds'.format(e.e.code, wait_period), file=sys.stderr)
            time.sleep(wait_period)
            wait_period *= 1.5
            return wait_period
        else:
            raise e

    # End of nested helper function

    wait_period = 2
    error_count = 0

    while True:
        try:
            return twitter_api_func(*args, **kw)
        except twitter.api.TwitterHTTPError as e:
            error_count = 0
            wait_period = handle_twitter_http_error(e, wait_period)
            if wait_period is None:
                return
        except URLError as e:
            error_count += 1
            time.sleep(wait_period)
            wait_period *= 1.5
            print("URLError encountered. Continuing.", file=sys.stderr)
            if error_count > max_errors:
                print("Too many consecutive errors...bailing out.", file=sys.stderr)
                raise
        except BadStatusLine as e:
            error_count += 1
            time.sleep(wait_period)
            wait_period *= 1.5
            print("BadStatusLine encountered. Continuing.", file=sys.stderr)
            if error_count > max_errors:
                print("Too many consecutive errors...bailing out.", file=sys.stderr)
                raise
#################

# code from Twitter Code Book to get friends and followers list for a given id or username:
def get_friends_followers_ids(twitter_api, screen_name=None, user_id=None,
                              friends_limit=maxint, followers_limit=maxint):
    # Must have either screen_name or user_id (logical xor)
    assert (screen_name != None) != (user_id != None), "Must have screen_name or user_id, but not both"

    # See http://bit.ly/2GcjKJP and http://bit.ly/2rFz90N for details
    # on API parameters

    get_friends_ids = partial(make_twitter_request, twitter_api.friends.ids,
                              count=5000)
    get_followers_ids = partial(make_twitter_request, twitter_api.followers.ids,
                                count=5000)

    friends_ids, followers_ids = [], []

    for twitter_api_func, limit, ids, label in [
        [get_friends_ids, friends_limit, friends_ids, "friends"],
        [get_followers_ids, followers_limit, followers_ids, "followers"]
    ]:

        if limit == 0: continue

        cursor = -1
        while cursor != 0:

            # Use make_twitter_request via the partially bound callable...
            if screen_name:
                response = twitter_api_func(screen_name=screen_name, cursor=cursor)
            else:  # user_id
                response = twitter_api_func(user_id=user_id, cursor=cursor)

            if response is not None:
                ids += response['ids']
                cursor = response['next_cursor']

            print('Fetched {0} total {1} ids for {2}'.format(len(ids), label, (user_id or screen_name)),
                  file=sys.stderr)

            # XXX: You may want to store data during each iteration to provide an
            # an additional layer of protection from exceptional circumstances

            if len(ids) >= limit or response is None:
                break

    # Do something useful with the IDs, like store them to disk...
    return friends_ids[:friends_limit], followers_ids[:followers_limit]
####################################################################

###########################################
# Code from Twitter CodeBook to get Twitter user profile for the particular user
def get_user_profile(twitter_api, screen_names=None, user_ids=None):
    # Must have either screen_name or user_id (logical xor)
    assert (screen_names != None) != (user_ids != None), "Must have screen_names or user_ids, but not both"

    items_to_info = {}

    items = screen_names or user_ids

    while len(items) > 0:

        # Process 100 items at a time per the API specifications for /users/lookup.
        # See http://bit.ly/2Gcjfzr for details.

        items_str = ','.join([str(item) for item in items[:100]])
        items = items[100:]

        if screen_names:
            response = make_twitter_request(twitter_api.users.lookup,
                                            screen_name=items_str)
        else:  # user_ids
            response = make_twitter_request(twitter_api.users.lookup,
                                            user_id=items_str)

        for user_info in response:
            if screen_names:
                items_to_info[user_info['screen_name']] = user_info
            else:  # user_ids
                items_to_info[user_info['id']] = user_info

    return items_to_info

# friends_ids, followers_ids = get_friends_followers_ids(twitter_api,screen_name=starting_point,friends_limit=5000,followers_limit=5000)
#
# print(len(friends_ids))
# print(len(followers_ids))
#
# reciprocal_friends = list(set(friends_ids).intersection(set(followers_ids)))
# print(reciprocal_friends)

######################################
# print(json.dumps(get_user_profile(twitter_api, user_ids=[1688460967]),indent=1))
# reci_prof=get_user_profile(twitter_api, user_ids=reciprocal_friends)
# reci_prof_coun={}
# for f in reci_prof.keys():
#     reci_prof_coun[f]=reci_prof[f]['followers_count']
# print(reci_prof_coun)
# top_5 = nlargest(5,reci_prof_coun, key=reci_prof_coun.get)
# print(top_5)
##############################################
# Make sure before u run the code delete the nodes.txt and edges.txt files
# Code written by me to Crawl the top 100 reciprocal friends of the user and store to file as nodes adn edges:
# Input staring point
# To crawl over user and get top5 recriporcal friends iterativley till it list reaches top 100
# Output: To store top 100 reciprocal friends as nodes into nodes.txt and corresponding relation between those as edges int egdes.txt.
def crawl_reciprocal_friends(twitter_api, screen_name, limit=5000):
    f1 = open("node.txt", "a")
    f2 = open("edges.txt", "a")
    # to start with starting point
    start_id = str(twitter_api.users.show(screen_name=screen_name)['id'])
    friends_ids, followers_ids = get_friends_followers_ids(twitter_api, user_id=start_id, friends_limit=5000,
                                                           followers_limit=5000)
    # // find the recriprocal friends
    reciprocal_friends = list(set(friends_ids).intersection(set(followers_ids)))
    reci_profiles = get_user_profile(twitter_api, user_ids=reciprocal_friends)
    reci_prof_coun = {}
    for f in reci_profiles.keys():
        reci_prof_coun[f] = reci_profiles[f]['followers_count']
    # print(reci_prof_coun)
    # calculate the top5 reciprocal friends
    top_5 = nlargest(5, reci_prof_coun, key=reci_prof_coun.get)
    # print(top_5)
    super_100=[]
    super_100=super_100+top_5
    # print("super_100",super_100)
    for i in top_5:
        f1.write(str(i)+"\n")
        f2.write(str(start_id)+":"+str(i)+"\n")
        # f2.write(str(i) + ":" + str(start_id) + "\n")
    #    iteratively repeat the step still it reachest atleat 100 nodes and rite back to file
    while(len(super_100)<200 ):
        top=[]
        flag=False
        for fid in top_5:
            friends, followers = get_friends_followers_ids(twitter_api, user_id=fid, friends_limit=5000,
                                                                   followers_limit=5000)
            reciprocal_friends_id = list(set(followers).intersection(set(friends)))
            reci_profiles1 = get_user_profile(twitter_api, user_ids=reciprocal_friends_id)
            reci_prof_coun1 = {}
            for f in reci_profiles1.keys():
                reci_prof_coun1[f] = reci_profiles1[f]['followers_count']
            # print("reci_prof_coun1",reci_prof_coun1)
            top=[]
            top=top+nlargest(5, reci_prof_coun1, key=reci_prof_coun1.get)
            #check adding top elements to top_5
            #add print
            print("top",top)
            for i in top:
                # print("writing")
                f1.write(str(i) + "\n")
                f2.write(str(fid) + ":" + str(i) + "\n")
                # f2.write(str(i) + ":" + str(fid) + "\n")
            super_100=super_100+top
            # print("super_100",len(super_100))
            print(super_100)
            if(len(super_100)>=200):
                flag=True
                break
        if(flag):
            break
        top_5=[]
        top_5=top_5+top
    f1.close()
    f2.close()
######################################
# construct a graph using nodes from nodes.txt and edges from edges.txt
# display the required output
def create_graph():
    f1 = open("node.txt", "r")
    n=f1.readlines()
    node=[]
    for i in range(0,len(n),1):
        node.append(int(n[i]))
    f2 = open("edges.txt", "r")
    e=f2.readlines()
    edge=[]
    fro=[]
    to=[]
    for i in range(0,len(e),1):
        a = e[i].split(':')
        fro.append(int(a[0]))
        to.append(int(a[1]))
    edge = list(zip(fro,to))
    print("nodes",node)
    print("edge",edge)

    G = nx.Graph()
    G.add_nodes_from(node)
    G.add_edges_from(edge)
    dia=nx.diameter(G)
    size=G.size()
    print("Size  : ",size)
    print("Number of edges : ",G.number_of_edges())
    print("Diameter : ",dia)
    avg=nx.average_shortest_path_length(G,weight=None,method='dijkstra')
    print("Average distance  : ",avg)
    f3 = open("output.txt", "w")
    f3.write("size  :"+str(size) + "\n")
    f3.write("Number of edges : "+str(G.number_of_edges())+"\n")
    f3.write("Diameter :  "+str(dia)+"\n" )
    f3.write("Average distance  : "+str(avg)+"\n")
    nx.draw(G,node_color='#A0CBE2', edge_color="#f49242")
    plt.show()
    f3.close()
# calling crawler and creating graph
crawl_reciprocal_friends(twitter_api,screen_name=starting_point,limit=5000)
create_graph()


################
brach3
changes focshncamxjidm
foresics science
#######################
