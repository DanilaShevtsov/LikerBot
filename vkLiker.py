import vk_api
import time
import json
import os
from icecream import ic
import random
import configparser


class System:
    # System methods for managing the work of bots
    def __init__(self):
        self.tokens = []
        self.active_bots = []
        self.ACCOUNTS = []
        self.VK = None

    def captcha_handler(self):
        '''Обработчик каптчи
        Если аккаунт попадает под каптчу, он переводится в инактив
        '''
        
        self.set_inactive_bot()
        self.VK = vk_api.VkApi(token=self.tokens[0], captcha_handler=self.captcha_handler).get_api()
        print('Bot was changed')
    
    def set_inactive_bot(self, bot_id=0):
        self.ACCOUNTS[self.ACCOUNTS.index(self.active_bots[bot_id])]['active'] = 0
        self.ACCOUNTS[self.ACCOUNTS.index(self.active_bots[bot_id])]['last_action_time'] = time.time()
        self.active_bots.pop(bot_id)
        self.tokens.pop(bot_id)

    def change_active_bot(self, bid):
        self.VK = vk_api.VkApi(token=self.tokens[bid], captcha_handler=self.captcha_handler).get_api()

    def set_owner(self):
        # Устанавливает пользователя для отправки лайков
        # Возвращает id пользователя
        acc_id = input('Account id: ')
        acc_id = self.get_id(acc_id)
        return acc_id

    def get_id(self, acc_id: str):
        # Функция для получения цифрового id из краткого или цифврого, который был введен пользователем
        # Возвращает цифровой id
        return sys.VK.users.get(user_ids=acc_id)[0]['id']

    def get_active_bots(self):
        '''Get a list of active bots
        Saves into Account.json information about self.ACCOUNTS
        '''
        global active_bots
        self.active_bots = []

        for acc_id, acc in enumerate(self.ACCOUNTS):
            if not self.ACCOUNTS[acc_id]['active']:
                if self.ACCOUNTS[acc_id]['last_action_time'] + int(config['ACTIONS']['COOLDOWN']) <= time.time():
                    self.ACCOUNTS[acc_id]['active'] = 1
                    self.ACCOUNTS[acc_id]['actions'] = self.ACCOUNTS[acc_id]['max_actions']
                    self.active_bots.append(self.ACCOUNTS[acc_id])
            else:
                self.active_bots.append(self.ACCOUNTS[acc_id])

        global tokens
        self.tokens = []

        for bot in self.active_bots:
            self.tokens.append(bot['token'])
        
        self.VK = vk_api.VkApi(token=self.tokens[0], captcha_handler=self.captcha_handler).get_api()
        self.save()   
        
    def save(self):
        with open(f'{os.path.dirname(__file__)}/self.ACCOUNTS.json', 'w') as f:
            json.dump(self.ACCOUNTS, f, separators=(',\n', ': '))

    def set_online_and_repost(self, bid=0):
        self.change_active_bot(bid)
        
        self.VK.account.setOnline()

        while True:
            time.sleep(10)
            uid = str(random.randint(1, 1000000000))
            pid = str(random.randint(3, 20))
            obj = f'wall{uid}_{pid}'
            print(f'https://vk.com/id{uid}?w={obj}')
            try:
                self.VK.wall.repost(object=obj)
                print('Post has been posted')
                break
            except Exception as exc:
                print('Post hasn\'t been posted')
                print(exc)

                continue

    def load(self):
        with open(f'{os.path.dirname(__file__)}/Accounts.json', 'r') as foa:
            self.ACCOUNTS = json.load(foa)
            if len(self.ACCOUNTS) == 0:
                print('There is no bots')
                exit()
                

class Photo():      
    def get_photo_ids(self, owner, count):
        ''' Функция получает цифровые id фото у owner в количестве count
        Возвращает id фоток
        
        '''
     
        photos = sys.VK.photos.getAll(owner_id=owner, extended=0, count=count)
        photo_IDS = []

        for photo in photos['items']:
            photo_IDS.append(photo['id'])
        
        return photo_IDS
    def is_liked(self, user_id, item_id):
        return sys.VK.photos.getById(photos=str(user_id)+'_'+str(item_id), extended=1)[0]['likes']['user_likes']

class Likes(Photo):
    def __init__(self):
        self.owner_id = 0

class OneLike(Likes):
    def __init__(self):
        pass
            
    def send(self, owner: int, count, bot_id=0):
        # Функия отправляет количество лайков (count) пользователю (owner)
        # Возвращает количество отправленных и неотправленных лайков
        self.sended = 0
        self.errors = 0

        photoIDS = self.get_photo_ids(owner, count)
        user = sys.VK.users.get(user_ids=owner)[0]

        for photo in photoIDS:
            try:
                for token_id, token in enumerate(sys.tokens):
                    if sys.active_bots[token_id]['actions'] > 0 and not self.is_liked(owner, photo):
                        liked_photo = sys.VK.likes.add(type='photo', owner_id=owner, item_id=photo)
                        print(f'Photo {photo} of {user["first_name"]} {user["last_name"]} has been liked: {liked_photo["likes"]}')
                        sys.active_bots[token_id]['actions'] -= 1
                        self.sended += 1
                        break
                    else:
                        print(f'Photo hasn\'t been liked by bot {token_id}') 
                    time.sleep(int(config['ACTIONS']['DELAY']))

            except Exception as exc:
                print(f'Photo {photo} could not be liked')
                print(exc)
                self.errors += 1

            
            sys.change_active_bot(0)

        return (self.sended, self.errors)

    def many_photos(self):
        # Начало отработки лайков
        # Место вхождения - МЕНЮ

        sys.get_active_bots()
        owner = sys.set_owner()
        count_of_photos = input("How many photos to like?\n")

        sended, error = self.send(owner, count_of_photos)
        print(f'Was sent {sended} likes\n{error} Errors\n') 

        sys.get_active_bots()
            
class ManyLikes(Likes):
    def __init__(self):
        pass
    
    def send(self, owner, photo_id, count):
        sended = 0
        errors = 0
        temp_count = count

        if not len(sys.active_bots):
            print('Bots ended')
            errors = count
            return (sended, errors)

        for token_id, token in enumerate(sys.tokens):
            if self.is_liked(owner, photo_id):
                print('The like of the bot is already here')
                sys.change_active_bot(token_id)
                continue
            if sys.active_bots[token_id]['actions'] > 0:
                try:
                    sys.VK.likes.add(type='photo', owner_id=owner, item_id=photo_id)
                    sys.active_bots[token_id]['actions'] -= 1
                    sended += 1
                    print('A like has been sent')
                    temp_count -= 1
                except:
                    print('A like hasn\'t been sent')
                    errors += 1
            else:
                print('Bot has no actions')
            sys.change_active_bot(token_id)

        if not count == temp_count + sended:
            print('Bots ended')
            errors = count - temp_count

        time.sleep(int(config['ACTIONS']['DELAY']))
        sys.save()
        return (sended, errors)

    def main_photo(self):
        sys.get_active_bots()

        while True:
            count = int(input(f'How many likes do you want? Maximum now: {len(sys.active_bots)}\n'))
            if count <= len(sys.active_bots):
                break
            else:
                print('Count is too many!')

        
        owner = sys.set_owner()
        
        user = sys.VK.users.get(user_ids=owner, fields='photo_id')[0]
        unclear_photo_id = user['photo_id']
        photo_id = int(unclear_photo_id.split('_')[1])

        done, errors = self.send(owner, photo_id, count)

        print(f'Was sent {done} likes on the your main photo\nErrors - {errors}')


    def the_photo(self):
        link = input('Enter a link on the photo: ')
        unclear_photo_id = link[link.find('?z=photo') + len('?z=photo'):link.find('%')]
        photo_id = unclear_photo_id.split('_')[1]
        sys.get_active_bots()

        while True:
            count = int(input(f'How many likes do you want? Maximum now: {len(sys.active_bots)}\n'))
            if count <= len(sys.active_bots):
                break
            else:
                print('Count is too many!')

        owner = sys.set_owner()
        #user = self.VK.users.get(user_ids=owner, fields='photo_id')[0]

        done, errors = self.send(owner, photo_id, count)
        print(f'Was sent {done} likes on {photo_id} photo\nErrors - {errors}')



one_like = OneLike()
many_likes = ManyLikes()
sys = System()

sys.load()

config = configparser.ConfigParser()
config.read(f'{os.path.dirname(__file__)}/config.ini')


# Ограничение на количество действий каждого бота в отдельности +
# Кулдаун в 24 часа, если действия закончились  +
# Лайк, снятие лайка тратят действия
# При загрузке активных аккаунтов, запускается проверка (если число действий == 0)
# Если кулдаун прошел, то перевести аккаунтв  список активных и добавить ему действия, и запостить на странице
# Сделать нормальный кофинг в формате ini   +


#BEGIN OF PROGRAM
if __name__ == '__main__':

    print('Welcome to VK Liker')

    while True:
        
        print('\n###################')
        print('1 - One like on photos')
        print('2 - Likes on the Main photo')
        print('3 - Likes on a photo')

        print('0 - Exit')
        print('###################\n')

        try:
            choice = int(input('Your choice: '))
        except Exception as exc:
            print(exc)
            print('!!!Invalid choice!!!\n')
            continue



        if choice == 1:
            one_like.many_photos()
        elif choice == 2:
            many_likes.main_photo()
        elif choice == 3:
            many_likes.the_photo()
        elif choice == 0:
            print('Goodbye :*')
            break
        else:
            print('Invalid input, it must be integer!\n')
