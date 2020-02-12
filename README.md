# BTCTurk API - Python Wrapper

BTCTurk API'nı efektif bir şekilde projelerinizde kullanabilmeniz için tasarlanmış bir python paketidir.

<!-- TABLE OF CONTENTS -->
## Table of Contents

* [Proje Hakkında](#about-the-project)
* [Başlarken](#getting-started)
  * [Gereklilikler](#prerequisites)
  * [Kurulum](#installation)
* [Kullanım](#usage)
* [Lisans](#license)
* [İletişim](#contact)



<!-- ABOUT THE PROJECT -->
## Proje Hakkında

[![Product Name Screen Shot][product-screenshot]](https://example.com)

BTCTurkApiWrapper

Bu paketi kullanarak BTCTurk hesabınızda:
* Kripto paraların güncel fiyatlarını anında öğrenebilir
* İstediğiniz alım ya da satım emrini girebilir (Stop, limit, market) ve emirlerinizi iptal edebilir
* Hesabınızdaki tüm açık emirleri görüntüleyip filtreleyebilir,
* Hesabınızın Cripto ve fiat işlem geçmişine ulaşabilirsiniz.


<!-- GETTING STARTED -->
## Başlarken

Paketi kullanabilmek için gereklilikler, kurulum ve kullanım kısmındaki açıklamalardan faydalanabilirsiniz.

### Gereklilikler
 
* BTCTurk API KEY (İzin isteyen işlemlerde)
```
https://www.btcturk.com/ApiAccess
```
Yukarıdaki linke giderek ilk önce giriş yapıp, sonra API KEY'inizi oluşturunuz.
Daha sonra API_KEY ve API_SECRET isimleri anahtarlarınızı bir yere kaydedin.

### Kurulum

BTCTurkApiWrapper'ı pip aracılığıyla kurabilirsiniz. 
```sh
sudo pip install btcturkapiwrapper 
```
Komutunu kullanarak paketi kurun.


<!-- USAGE EXAMPLES -->
## Kullanım

BTCTurkApiWrapper Client'ini projenize import edin
```py
from BTCTurkApiWrapper.client import Client
```
Bundan sonra Client'den bir nesne oluşturmanız yeterli olacaktır.
Fiyat takibi gibi hesap izni gerektirmeyen işlemler için;
```py
client = Client()
```
yeterli olacaktır. Fakat alım satım gibi hesap izni gerektiren işlemler için;
```py
client = Client(api_key, api_secret)
```
BTCTurk'ten aldığınız API KEY VE API SECRET'ı Client'e parametre olarak vermeniz gerekmektedir.

Yapabileceğiniz birkaç işlem:
Bitcoin ve diğer kriptoların fiyatları için tick fonksiyonunu kullanın
```py
btc_price = client.tick('BTC_TRY') # ETH_TRY, XRP_TRY vs...
```



<!-- LICENSE -->
## License

Bu python paketini herkes kullanabilir, değiştirebilir ve çoğaltabilir. Detaylı bilgi için LICENSE.txt'ye bakın



<!-- CONTACT -->
## İletişim

Miraç Baydemir -  omermirac59@gmail.com

Project Link: [https://github.com/outlier-1/btcturkapi-python/](https://github.com/outlier-1/btcturkapi-python/)



