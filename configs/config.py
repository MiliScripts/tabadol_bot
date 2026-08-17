import yaml
with open("configs/config.yml",'r') as file :
    data = yaml.safe_load(file)




import yaml
with open("configs/config.yml",'r') as file :
    data = yaml.safe_load(file)

api_id = data['API_ID']
api_hash = data['API_HASH']
bot_token =  data['BOT_TOKEN']
admins = data['ADMINS']
force_join_channel_link ="https://t.me/TabadolArz_Trades"
force_join_channel_id = -1002065261878
bot_id = "@TabadolArz_Robot"
channel_address = "https://t.me/TabadolArz_Trades/"
support_chat_link = "https://t.me/TabadolArz_Support"
report_channel = -1002246606763
group_link = "https://t.me/TabadolArz_Trades"
master_user = 982290123
discussion_send_chat = -1002065261878
comments_url = "https://t.me/TabadolArz_Comments"




# custom forward channels 
class CustomChannels(object):
    euro_channels = {
        "spain" : -1002457142632 ,
        "germany" : -1002384522064, 
        "italy" : -1002349489420,
        "france" : -1002329905875,
        "cyprus" : -1002288647780,
        "meow" : -1002339012039
    }
    
    pond_channels = {
        "uk" : -1002481520621
    }
    
    cny_channels = {
        "alibaba" : -1002369021803
    }
    
    usd_channels = {
        "la" : -1002263723875,
         "meow" : -1002339012039
        
    }
    usd_canada_channels = {
        "ca" : -1002340663316
    }
    
    aed_channels = {
        "dubai" : -1002347581386
    }
    
    kron_channels = {
        "denmark" : -1002398357287
    }
    
    swedn_kron = {
        "sweden" : -1002339012039
    }
    
    
    lir_channels = {
        "turkey" : -1002287827533,
        "cyprus" : -1002288647780
    }
    
    thether_Channels = {
        "gap" : -1002343881600
    }

    rub_channels = {
        "russia" : -1002347581386
    }
    


cchannels = CustomChannels()

