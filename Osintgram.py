from InstagramAPI import InstagramAPI 
from geopy.geocoders import Nominatim
import sys
import argparse
import datetime
from collections import OrderedDict
import json
from prettytable import PrettyTable
import urllib
from requests.exceptions import HTTPError
import printcolors as pc



class Osintgram:
    api = None
    geolocator = Nominatim()
    user_id = None
    target_id = None
    is_private = True
    target = ""
    writeFile = False

    def __init__(self, target):
        u = self.__getUsername__()
        p = self.__getPassword__()
        self.api = InstagramAPI(u, p)
        print("\nAttempt to login...")
        self.api.login()
        self.setTarget(target)


    def setTarget(self, target):
        self.target = target
        user = self.getUser(target)
        self.target_id = user['id']
        self.is_private = user['is_private']
        self.__printTargetBanner__()


    def __getUsername__(self):
        u = open("config/username.conf", "r").read()
        u = u.replace("\n", "")
        return u
    
    def __getPassword__(self):
        p = open("config/pw.conf", "r").read()
        p = p.replace("\n", "")
        return p

    def __getAdressesTimes__(self, id):
        only_id = {} 
        photos = []
        a = None 
        while True:
            if (a == None):
                self.api.getUserFeed(id)
                a = self.api.LastJson['items']
                only_id = self.api.LastJson
            else:
                self.api.getUserFeed(id, only_id['next_max_id'])
                only_id = self.api.LastJson
                a = self.api.LastJson['items']
                
            photos.append(a)

            if not 'next_max_id' in only_id:
                break
        
        
        locations = {}

        for i in photos:
            for j in i:
                if 'lat' in j.keys():
                    lat = j.get('lat')
                    lng = j.get('lng')

                    locations[str(lat) + ', ' + str(lng)] = j.get('taken_at')

        address = {}
        for k,v in locations.items():
            details = self.geolocator.reverse(k)
            unix_timestamp = datetime.datetime.fromtimestamp(v)
            address[details.address] = unix_timestamp.strftime('%Y-%m-%d %H:%M:%S')


        sort_addresses = sorted(address.items(), key=lambda p: p[1], reverse=True) 

        return sort_addresses 

    def __printTargetBanner__(self):
        pc.printout("\nLogged as ", pc.GREEN)
        pc.printout(self.api.username, pc.CYAN)
        pc.printout(" (" + str(self.api.username_id) + ") ")
        pc.printout("target: ", pc.GREEN)
        pc.printout(str(self.target), pc.CYAN)
        pc.printout(" (private: " + str(self.is_private) + ")")
        print('\n')

    def setWriteFile(self, bool):
        if(bool):
            pc.printout("Write to file: ")
            pc.printout("enabled", pc.GREEN)
            pc.printout("\n")
        else:
            pc.printout("Write to file: ")
            pc.printout("disabled", pc.RED)
            pc.printout("\n")

        self.writeFile = bool


    def __getUserFollowigs__(self, id):
        following = []
        next_max_id = True
        while next_max_id:
            # first iteration hack
            if next_max_id is True:
                next_max_id = ''
            _ = self.api.getUserFollowings(id, maxid=next_max_id)
            following.extend(self.api.LastJson.get('users', []))
            next_max_id = self.api.LastJson.get('next_max_id', '')

        len(following)
        unique_following = {
            f['pk']: f
            for f in following
        }
        len(unique_following)
        return following

    def __getTotalFollowers__(self, user_id):
        followers = []
        next_max_id = True
        while next_max_id:
            # first iteration hack
            if next_max_id is True:
                next_max_id = ''

            _ = self.api.getUserFollowers(user_id, maxid=next_max_id)
            followers.extend(self.api.LastJson.get('users', []))
            next_max_id = self.api.LastJson.get('next_max_id', '')

        return followers

        
    def getHashtags(self):
        if(self.is_private):
            pc.printout("Impossible to execute command: user has private profile\n", pc.RED)
            return
        
        pc.printout("Searching for target hashtags...\n")

        text = []
        only_id = {}
        a = None 
        hashtags = []
        counter = 1
        while True:
            if (a == None):
                self.api.getUserFeed(self.target_id)
                a = self.api.LastJson['items']
                only_id = self.api.LastJson
                with open('data.json', 'w') as outfile:
                    json.dump(only_id, outfile)
                
            else:
                self.api.getUserFeed(self.target_id, only_id['next_max_id'])
                only_id = self.api.LastJson
                a = self.api.LastJson['items']

            try:
                for i in a:
                    c = i.get('caption', {}).get('text')
                    text.append(c)
                    counter = counter +1
            except AttributeError:
                pass

            if not 'next_max_id' in only_id:
                break

        hashtag_counter = {}

        for i in text:
            for j in i.split():
                if j.startswith('#'):
                    hashtags.append(j.encode('UTF-8'))

        for i in hashtags:
            if i in hashtag_counter:
                hashtag_counter[i] += 1
            else:
                hashtag_counter[i] = 1

        sortE = sorted(hashtag_counter.items(), key=lambda value: value[1], reverse=True)

        if(self.writeFile):
            file_name = "output/" + self.target + "_hashtags.txt"
            file = open(file_name, "w")
            for k,v in sortE:
                file.write(str(v) + ". " + str(k.decode('utf-8'))+"\n")
            file.close()
            

        for k,v in sortE:
            print( str(v) + ". " + str(k.decode('utf-8')))
        


    def getTotalLikes(self):
        if(self.is_private):
            pc.printout("Impossible to execute command: user has private profile\n", pc.RED)
            return

        pc.printout("Searching for target total likes...\n")

        like_counter = 0
        only_id = {}
        a = None 
        counter = 0
        while True:
            if (a == None):
                self.api.getUserFeed(self.target_id)
                a = self.api.LastJson['items']
                only_id = self.api.LastJson 
            else:
                self.api.getUserFeed(self.target_id, only_id['next_max_id']) 
                only_id = self.api.LastJson
                a = self.api.LastJson['items']
            try:
                for i in a:
                    c = int(i.get('like_count'))
                    like_counter += c
                    counter = counter +1
            except AttributeError:
                pass

            if not 'next_max_id' in only_id:
                break

        if(self.writeFile):
            file_name = "output/" + self.target + "_likes.txt"
            file = open(file_name, "w")
            file.write(str(like_counter) + " likes in " + str(counter) + " posts\n")
            file.close()

        pc.printout(str(like_counter), pc.MAGENTA)
        pc.printout(" likes in " + str(counter) + " posts\n")
    
    def getTotalComments(self):
        if(self.is_private):
            pc.printout("Impossible to execute command: user has private profile\n", pc.RED)
            return
        
        pc.printout("Searching for target total comments...\n")

        comment_counter = 0
        only_id = {}
        a = None 
        counter = 0
        while True:
            if (a == None):
                self.api.getUserFeed(self.target_id)
                a = self.api.LastJson['items']
                only_id = self.api.LastJson
            else:
                self.api.getUserFeed(self.target_id, only_id['next_max_id'])
                only_id = self.api.LastJson
                a = self.api.LastJson['items']
            try:
                for i in a:
                    c = int(i.get('comment_count'))
                    comment_counter += c
                    counter = counter +1
            except AttributeError:
                pass

            if not 'next_max_id' in only_id:
                break

        if(self.writeFile):
            file_name = "output/" + self.target + "_comments.txt"
            file = open(file_name, "w")
            file.write(str(comment_counter) + " comments in " + str(counter) + " posts\n")
            file.close()

        pc.printout(str(comment_counter), pc.MAGENTA)
        pc.printout(" comments in " + str(counter) + " posts\n")

    def getPeopleTaggedByUser(self):
        pc.printout("Searching for users tagged by target...\n")
        
        ids = []
        username = []
        full_name = []
        post = []
        only_id = {}
        a = None 
        counter = 1
        while True:
            if (a == None):
                self.api.getUserFeed(self.target_id)
                a = self.api.LastJson['items']
                only_id = self.api.LastJson

                
            else:
                self.api.getUserFeed(self.target_id, only_id['next_max_id'])
                only_id = self.api.LastJson
                a = self.api.LastJson['items']

            try:
                for i in a:
                    if "usertags" in i:
                        c = i.get('usertags').get('in')
                        for cc in c:
                            if cc.get('user').get('pk') not in ids:
                                ids.append(cc.get('user').get('pk'))
                                username.append(cc.get('user').get('username'))
                                full_name.append(cc.get('user').get('full_name'))
                                post.append(1)
                            else:
                                index = ids.index(cc.get('user').get('pk'))
                                post[index] += 1
                            counter = counter +1
            except AttributeError as ae:
                pc.printout("\nERROR: an error occurred: ", pc.RED)
                print(ae)
                print("")
                pass

            if not 'next_max_id' in only_id:
                break

        if len(ids) > 0:
            t = PrettyTable()

            t.field_names = ['Posts', 'Full Name', 'Username', 'ID']
            t.align["Posts"] = "l"
            t.align["Full Name"] = "l"
            t.align["Username"] = "l"
            t.align["ID"] = "l"
            
            pc.printout("\nWoohoo! We found " + str(len(ids)) + " (" + str(counter) + ") users\n", pc.GREEN)

            for i in range(len(ids)):
                t.add_row([post[i], full_name[i], username[i], str(ids[i])])

            if(self.writeFile):
                file_name = "output/" + self.target + "_tagged.txt"
                file = open(file_name, "w")
                file.write(str(t))
                file.close()

            print(t)
        else:
            pc.printout("Sorry! No results found :-(\n", pc.RED)



    def getAddrs(self):
        if(self.is_private):
            pc.printout("Impossible to execute command: user has private profile\n", pc.RED)
            return

        pc.printout("Searching for target address... this may take a few minutes...\n")
        addrs = self.__getAdressesTimes__(self.target_id)
        t = PrettyTable()

        t.field_names = ['Post', 'Address', 'time']
        t.align["Post"] = "l"
        t.align["Address"] = "l"
        t.align["Time"] = "l"
        pc.printout("\nWoohoo! We found " + str(len(addrs)) + " addresses\n", pc.GREEN)

        i = 1
        for address, time in addrs:
            t.add_row([str(i), address, time])
            i = i + 1

        if(self.writeFile):
                file_name = "output/" + self.target + "_addrs.txt"
                file = open(file_name, "w")
                file.write(str(t))
                file.close()

        print(t)

    def getFollowers(self):
        if(self.is_private):
            pc.printout("Impossible to execute command: user has private profile\n", pc.RED)
            return

        pc.printout("Searching for target followers...\n")

        followers = self.__getTotalFollowers__(self.target_id)
        t = PrettyTable(['ID', 'Username', 'Full Name'])
        t.align["ID"] = "l"
        t.align["Username"] = "l"
        t.align["Full Name"] = "l"
        
        for i in followers:
            t.add_row([str(i['pk']), i['username'], i['full_name']])

        if(self.writeFile):
                file_name = "output/" + self.target + "_followers.txt"
                file = open(file_name, "w")
                file.write(str(t))
                file.close()        

        print(t)

    def getFollowings(self):
        if(self.is_private):
            pc.printout("Impossible to execute command: user has private profile\n", pc.RED)
            return

        pc.printout("Searching for target followings...\n")

        followings = self.__getUserFollowigs__(self.target_id)
        t = PrettyTable(['ID', 'Username', 'Full Name'])
        t.align["ID"] = "l"
        t.align["Username"] = "l"
        t.align["Full Name"] = "l"

        for i in followings:
            t.add_row([str(i['pk']), i['username'], i['full_name']])

        if(self.writeFile):
                file_name = "output/" + self.target + "_followings.txt"
                file = open(file_name, "w")
                file.write(str(t))
                file.close()

        print(t)

    def getUser(self, username):
        try:
            content = urllib.request.urlopen("https://www.instagram.com/" + username + "/?__a=1" )
        except urllib.error.HTTPError as err: 
            if(err.code == 404):
                print("Oops... " + username + " non exist, please enter a valid username.")
                sys.exit(2)

        data = json.load(content)

        if(self.writeFile):
            file_name = "output/" + self.target + "_user_id.txt"
            file = open(file_name, "w")
            file.write(str(data['graphql']['user']['id']))
            file.close()

        user = dict()
        user['id'] = data['graphql']['user']['id']
        user['is_private'] = data['graphql']['user']['is_private']
        
        return user

    def getUserInfo(self):
        try:
            content = urllib.request.urlopen("https://www.instagram.com/" + str(self.target) + "/?__a=1" )
        except urllib.error.HTTPError as err: 
            if(err.code == 404):
                print("Oops... " + str(self.target) + " non exist, please enter a valid username.")
                sys.exit(2)

        data = json.load(content)
        data = data['graphql']['user']

        pc.printout("[ID] ", pc.GREEN)
        pc.printout(str(data['id']) + '\n')
        pc.printout("[FULL NAME] ", pc.RED)
        pc.printout(str(data['full_name']) + '\n')
        pc.printout("[BIOGRAPHY] ", pc.CYAN)
        pc.printout(str(data['biography']) + '\n')
        pc.printout("[FOLLOWED] ", pc.GREEN)
        pc.printout(str(data['edge_followed_by']['count']) + '\n')
        pc.printout("[FOLLOW] ", pc.BLUE)
        pc.printout(str(data['edge_follow']['count']) + '\n')
        pc.printout("[BUSINESS ACCOUNT] ", pc.RED)
        pc.printout(str(data['is_business_account']) + '\n')
        if data['is_business_account'] == True:
            pc.printout("[BUSINESS CATEGORY] ")
            pc.printout(str(data['business_category_name']) + '\n')
        pc.printout("[VERIFIED ACCOUNT] ", pc.CYAN)
        pc.printout(str(data['is_verified']) + '\n')

    def getPhotoDescription(self):
        if(self.is_private):
            pc.printout("Impossible to execute command: user has private profile\n", pc.RED)
            return

        content = self.api.SendRequest2(self.target + '/?__a=1')
        data = self.api.LastJson
        dd = data['graphql']['user']['edge_owner_to_timeline_media']['edges']

        if len(dd) > 0:
            pc.printout("\nWoohoo! We found " + str(len(dd)) + " descriptions\n", pc.GREEN)

            count = 1

            t = PrettyTable(['Photo', 'Description'])
            t.align["Photo"] = "l"
            t.align["Description"] = "l"
            
            for i in dd:
                node = i.get('node')
                t.add_row([str(count), node.get('accessibility_caption')])
                count += 1

            if(self.writeFile):
                file_name = "output/" + self.target + "_photodes.txt"
                file = open(file_name, "w")
                file.write(str(t))
                file.close()                

                
            print(t)
        else:
            pc.printout("Sorry! No results found :-(\n", pc.RED)

    def getUserPhoto(self):
        if(self.is_private):
            pc.printout("Impossible to execute command: user has private profile\n", pc.RED)
            return

        limit = -1
        pc.printout("How many photos you want to download (default all): ", pc.YELLOW)
        l = input()
        try:
            if l == "":
                pc.printout("Downloading all photos avaible...\n")
            else:
                limit = int(l)
                pc.printout("Downloading " + l + " photos...\n")

        except ValueError:
            pc.printout("Wrong value entered\n", pc.RED)
            return

        
        a = None 
        counter = 0
        while True:
            if (a == None):
                self.api.getUserFeed(self.target_id)
                a = self.api.LastJson['items']
                only_id = self.api.LastJson 
                
            else:
                self.api.getUserFeed(self.target_id, only_id['next_max_id'])
                only_id = self.api.LastJson
                a = self.api.LastJson['items']

            try:
                for item in a:
                    if counter == limit:
                        break
                    if "image_versions2" in item:
                        counter = counter + 1
                        url = item["image_versions2"]["candidates"][0]["url"]
                        photo_id = item["id"]
                        end = "output/" + self.target +  "_" + photo_id +  ".jpg"
                        urllib.request.urlretrieve(url, end) 
                        sys.stdout.write("\rDownloaded %i" % counter)
                        sys.stdout.flush()   
                    else:
                        carousel = item["carousel_media"]
                        for i in carousel:
                            if counter == limit:
                                break
                            counter = counter + 1                     
                            url = i["image_versions2"]["candidates"][0]["url"]
                            photo_id = i["id"]
                            end = "output/" + self.target +  "_" + photo_id +  ".jpg"
                            urllib.request.urlretrieve(url, end)
                            sys.stdout.write("\rDownloaded %i" % counter)
                            sys.stdout.flush()   

            except AttributeError:
                pass
            
            except KeyError:
                pass

            if not 'next_max_id' in only_id:
                break
            
        sys.stdout.write(" photos")
        sys.stdout.flush()         

        pc.printout("\nWoohoo! We downloaded " + str(counter) + " photos (saved in output/ folder) \n", pc.GREEN)

    def getCaptions(self):
        if(self.is_private):
            pc.printout("Impossible to execute command: user has private profile\n", pc.RED)
            return

        pc.printout("Searching for target captions...\n")
        
        a = None 
        counter = 0
        captions = []
        while True:
            if (a == None):
                self.api.getUserFeed(self.target_id)
                a = self.api.LastJson['items']
                only_id = self.api.LastJson 
                
            else:
                self.api.getUserFeed(self.target_id, only_id['next_max_id']) 
                only_id = self.api.LastJson
                a = self.api.LastJson['items']

            try:
                for item in a:
                    if "caption" in item:
                        if item["caption"] != None:
                            text = item["caption"]["text"]
                            captions.append(text)
                            counter = counter + 1
                            sys.stdout.write("\rFound %i" % counter)
                            sys.stdout.flush()

            except AttributeError:
                pass
            
            except KeyError:
                pass

            if not 'next_max_id' in only_id:
                break
            
        sys.stdout.write(" captions")
        sys.stdout.flush()  

        if counter > 0:
            pc.printout("\nWoohoo! We found " + str(counter) + " captions\n", pc.GREEN)

               

            if(self.writeFile):
                file_name = "output/" + self.target + "_captions.txt"
                file = open(file_name, "w")
                for s in captions:
                    file.write(s + "\n")
                file.close()

            for s in captions:
                print(s + "\n")

        else:
            pc.printout("Sorry! No results found :-(\n", pc.RED)
        
        return

    def getMediaType(self):
        if(self.is_private):
            pc.printout("Impossible to execute command: user has private profile\n", pc.RED)
            return

        pc.printout("Searching for target captions...\n")
        
        a = None 
        counter = 0
        photo_counter = 0
        video_counter = 0
        
        while True:
            if (a == None):
                self.api.getUserFeed(self.target_id)
                a = self.api.LastJson['items']
                only_id = self.api.LastJson
                
            else:
                self.api.getUserFeed(self.target_id, only_id['next_max_id']) 
                only_id = self.api.LastJson
                a = self.api.LastJson['items']

            try:
                for item in a:
                    if "media_type" in item:
                        if item["media_type"] == 1:
                            photo_counter = photo_counter + 1
                        elif item["media_type"] == 2:
                            video_counter = video_counter + 1

                        counter = counter + 1
                        sys.stdout.write("\rChecked %i" % counter)
                        sys.stdout.flush()

            except AttributeError:
                pass
            
            except KeyError:
                pass

            if not 'next_max_id' in only_id:
                break
            
        sys.stdout.write(" posts")
        sys.stdout.flush()  

        if counter > 0:              

            if(self.writeFile):
                file_name = "output/" + self.target + "_mediatype.txt"
                file = open(file_name, "w")
                file.write(str(photo_counter) + " photos and " + str(video_counter) \
                        + " video posted by target\n")
                file.close()


            pc.printout("\nWoohoo! We found " + str(photo_counter) + " photos and " + str(video_counter) \
                        + " video posted by target\n", pc.GREEN)

        else:
            pc.printout("Sorry! No results found :-(\n", pc.RED)
        
        return
    
    def getUserPropic(self):
        try:
            content = urllib.request.urlopen("https://www.instagram.com/" + str(self.target) + "/?__a=1" )
        except urllib.error.HTTPError as err: 
            if(err.code == 404):
                print("Oops... " + str(self.target) + " non exist, please enter a valid username.")
                sys.exit(2)

        data = json.load(content)

        URL = ""

        uurl = data["graphql"]["user"]
        if "profile_pic_url_hd" in uurl:
            URL = data["graphql"]["user"]["profile_pic_url_hd"]
        else:
            URL = data["graphql"]["user"]["profile_pic_url"]

        if URL != "":
            end = "output/" + self.target +  "_propic.jpg"
            urllib.request.urlretrieve(URL, end)
            pc.printout("Target propic saved in output folder\n", pc.GREEN)

        else:
            pc.printout("Sorry! No results found :-(\n", pc.RED)

    def getUserStories(self):
        if(self.is_private):
            pc.printout("Impossible to execute command: user has private profile\n", pc.RED)
            return

        pc.printout("Searching for target stories...\n")

        endpoint = 'feed/user/{id!s}/story/'.format(**{'id': self.target_id})
        content = self.api.SendRequest(endpoint)
        data = self.api.LastJson
        counter = 0
        
        if data['reel'] != None: # no stories avaibile
            for i in data['reel']['items']:
                story_id = i["id"]
                if i["media_type"] == 1: # it's a photo
                    url = i['image_versions2']['candidates'][0]['url']
                    end = "output/" + self.target +  "_" + story_id +  ".jpg"
                    urllib.request.urlretrieve(url, end)
                    counter += 1
                
                elif i["media_type"] == 2: # it's a gif or video
                    url = i['video_versions'][0]['url']
                    end = "output/" + self.target +  "_" + story_id +  ".mp4"
                    urllib.request.urlretrieve(url, end)
                    counter += 1

        if counter > 0:
            pc.printout(str(counter) + " target stories saved in output folder\n", pc.GREEN)
        else:
            pc.printout("Sorry! No results found :-(\n", pc.RED)
            
    def changeTarget(self):
        pc.printout("Insert new target username: ", pc.YELLOW)
        l = input()
        self.setTarget(l)
        
        return
