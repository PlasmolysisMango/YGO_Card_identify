from sys import argv
from PIL import Image, ImageFile
import dhash
import sqlite3

ImageFile.LOAD_TRUNCATED_IMAGES = True
Image.MAX_IMAGE_PIXELS = None

filepath = argv[1]

show_search_limit=5

#ygo card image area y1-y2
y_1=(130/700)
y_2=(490/700)

#ygo card image area x1-x2
x_1=(60/480)
x_2=(424/480)

c_dhash_dir = '.\card_image_check.db'
c_ygo_dir = '.\cards.cdb'

def get_card_img_basic_dhash(path) -> str:
    _img=Image.open(path)
    _img = _img.resize((480,700))
    
    _y_1=int(_img.height*y_1)
    _y_2=int(_img.height*y_2)
    _x_1= int(_img.width*x_1)
    _x_2=int(_img.width*x_2)

    _img = _img.crop((_x_1,_y_1,_x_2,_y_2))
    row, col = dhash.dhash_row_col(_img)
    _img.close()
    _temp_dhash=dhash.format_hex(row, col)

    return _temp_dhash

def get_card_img_dhash_cache():
    conn = sqlite3.connect(c_dhash_dir)
    c = conn.cursor()
    
    c.execute(''' SELECT count(name) FROM sqlite_master WHERE type='table' AND name='CardDhash' ''')
    
    if c.fetchone()[0]!=1 :  
        print("No table find")
        conn.close()
        return None
    c.execute(''' SELECT count(*) FROM CardDhash ''')
    if c.fetchone()[0]==0:
        print("No data Init")
        conn.close()
        return None
    
    cache=[]
    cursor = conn.execute("SELECT code,dhash from CardDhash")
    for row in cursor:
        cache.append(
            {
                'code':row[0],
                'dhash':row[1]
            }
        )

    conn.close()
    return cache

def hammingDist(s1, s2):
    assert len(s1) == len(s2)
    return sum([ch1 != ch2 for ch1, ch2 in zip(s1, s2)])

def translate(cache:list, dhash_info:str) -> None:
    results=[]
    
    for _img_dhash in cache:
        d_score = 1 - hammingDist(dhash_info,_img_dhash['dhash']) * 1. / (32 * 32 / 4)
        
        results.append({
                'card':_img_dhash['code'],
                'score':d_score
            })
                
        results.sort(key=lambda x:x['score'],reverse=True)
        
        if len(results)>show_search_limit:
            results=results[:show_search_limit]  
    
    ygo_sql=sqlite3.connect(c_ygo_dir)
    for card in results:
        try:
            cursor = ygo_sql.execute(f"SELECT name,desc from texts WHERE id='{card['card']}' LIMIT 1")
        except:
            print("读取ygo数据库异常,是不是没有将card.cdb放进来")
            return
        if cursor.arraysize!=1:
            print(f"card {card['card']} not found")
            ygo_sql.close()
            return
        data=cursor.fetchone()
        card['name']=data[0]
        card['desc']=data[1]
    ygo_sql.close()
    print("识别结果")
    print('\n----------------------------------\n')
    for card in results:
        if card['score']<0.93:
            print("【相似度匹配过低】")
        print(f"{card['name']}(密码:{card['card']},相似度:{card['score']})\n{card['desc']}\n")
        print('----------------------------------\n')

def mainloop():
    hash_info = get_card_img_basic_dhash(filepath)
    cache = get_card_img_dhash_cache()
    translate(cache, hash_info)

if __name__ == '__main__':
    mainloop()
    input()