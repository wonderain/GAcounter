from ELO import *

match_path='宝宝局'
if not os.path.exists(match_path):
    sys.exit(1)

record=json_read(match_path+'/record.json')
json_write(match_path+'/record.json',{})
for i in os.listdir(match_path+'/players'):
    os.remove(match_path+'/players/'+i)
for index in range(len(record)):
    elo_open(match_path).input_new_record(record[str(index+1)])
