default["bigtent"]["client_session_secret"] = "Rrop8eT9clHDkJUBPJnpQta6iWxkPCRC"
default["bigtent"]["browserid_server"] = "https://login.anosrep.org"
default["bigtent"]["issuer"] = "yahoo.login.anosrep.org"
# Note these is an example key pair that will be overwritten by your actual keypair
default["bigtent"]["secretkey"] = "{\"algorithm\":\"RS\",\"n\":\"13828746125963425712927708562882880353632442547786023389523021048038884491682391284229598983495041058639375094697704400954756185503360655045139723469792264329266260172544950196287648829149134511817887182510221538031586091409090624038117202677349271667965542476527175948454647970257908540410342478095776627513116614813472232084906761354187154794897213948835085496352376645317856390552435840215888192861658882299733436099254594944674259826979791890133593787636917223591755821205318583929651430762177959790567722240948805696743915160796647716403603382930388365243172543464571313959371711675357254080203103299937117094921\",\"e\":\"65537\",\"d\":\"4616404591968320608929801607317265916608489525923716674794156804385228419198732876335126212077216050184052494343597920015993344621244860324359779514962771548830236966216616878929172545037532460282767532522981320613623457098251135583043596139204531265571358748515518797019863409879953660483352499134525551317982931799357825594512686582314284901811081561902799953862900189315123232285349789406016505602414988555384988962936177662738912315540100587567293066480479613591023667543577418341808728982469915807200613830679085415695047583202404396569993384483505786606045671267105657387796346961551765384657222648672205434681\"}"
default["bigtent"]["publickey"] = "{\"algorithm\":\"RS\",\"n\":\"13828746125963425712927708562882880353632442547786023389523021048038884491682391284229598983495041058639375094697704400954756185503360655045139723469792264329266260172544950196287648829149134511817887182510221538031586091409090624038117202677349271667965542476527175948454647970257908540410342478095776627513116614813472232084906761354187154794897213948835085496352376645317856390552435840215888192861658882299733436099254594944674259826979791890133593787636917223591755821205318583929651430762177959790567722240948805696743915160796647716403603382930388365243172543464571313959371711675357254080203103299937117094921\",\"e\":\"65537\"}"
default["bigtent"]["pin_code_session_secret"] = "SFUnRNhWd57Oia8MYpzOPW310E1DJRPn"

# Setting these to false bypasses the proxy
# default["proxy"]["host"] = "proxy.example.com"
# default["proxy"]["port"] = 3128
default["proxy"]["host"] = false
default["proxy"]["port"] = false

default["bigtent"]["rpms"]["bigtent"] = 'browserid-bigtent-0.2013.05.29-5.el6_116978.x86_64.rpm'
default["bigtent"]["rpms"]["certifier"] = 'browserid-certifier-0.2013.02.14-2.el6.x86_64.rpm'
default["bigtent"]["rpms"]["nodejs"] = 'nodejs-0.8.26-1.el6.x86_64.rpm'
