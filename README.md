# DistributedScrapper

En la implementación del proyecto se hace uso de la librería de Python Pyro4, la cual permite de una forma sencilla acceder desde un nodo a los métodos y propiedades de otro nodo que se encuentra en la red. Para acceder a dichos nodos, se necesita conocer su 'uri' pero esto resulta engorroso, por tanto se utilizó un servidor de nombres que permitió asignarle un identificador a cada nodo a partir de su ip y su puerto y con este crear su proxy.

El proyecto esta conformado por tres tipos de nodos diferentes: chord, scrapper y client. El flujo del sistema se comporta de la siguiente forma: Un cliente quiere obtener el html de una url y/o de las url que se encuentran dentro del mismo con una profundidad dada. El cliente le envía esta url a un nodo scrapper del cual conoce su ip y su puerto, este al recibirla la hashea y se la envía a un nodo chord del cual conoce su ip y su puerto. Si este nodo chord logra encontrar esta llave en el sistema entonces retorna su valor, en caso contrario el scrapper obtiene el html de internet y le pide al nodo chord guardarla para futuras consultas. Luego según la profundidad introducida por el cliente, el scrapper debe o no procesar las url internas; en caso de que sí, decide cuáles nodos scrapper conectados a la red serán los encargados de procesar dichas urls, y le pide a cada uno que repita el mismo procedimiento para obtener el html y las urls internas de la url que le tocó procesar. Una vez que cada nodo encargado de una url termina retorna los html al nodo scrapper que lo invocó, así hasta llegar al nodo scrapper original y este se los envía al cliente. Por último el cliente guarda el html de cada url en archivos distintos.

Para lograr que un nodo scrapper pueda distribuir las consultas de url con los demás nodos, cada uno de ellos conoce a todos los scrappers existentes en la red; para esto cada uno tendrá una lista de todos los que están conectados. Un nodo recién unido a la red guarda los id de los nodos que tiene guardado el  scrapper al cual le está haciendo la petición de join; luego cada uno de los scrappers presentes en la red suman a su lista el nuevo nodo. Esta lista se actualiza constantemente eliminando los nodos no conectados, por tanto, el primer nodo scrapper solo se tiene a si mismo en su lista hasta que llega uno nuevo y ambos se actualizan. Como bien se menciona, un nodo scrapper debe conocer un nodo chord para poder buscar las urls con sus htmls guardados, entonces para evitar que si este nodo chord se cae durante una consulta hecha por un cliente dicha consulta se pierda, cada nodo scrapper no solo guardará el id de su nodo chord sino que también tendrá guardada su lista de sucesores para en caso de que el nodo chord se caiga continuar con la consulta utilizando uno de sus sucesores activos.  

Los nodos chord se van a encargar de tener almacenado el html de las url que el cliente consulte al sistema, simulando el comportamiento de una caché. Se implementaron las funcionalidades descritas en el documento ¨Chord: A Scalable Peer-to-peer Lookup Service for Internet Applications¨ presente en la bibliografía. Entre dichas funcionalidades se encuentra: unir un nodo a la red, actualizar su información, que los mismos puedan abandonar la red sin que el sistema colapse, además de las funciones encargadas del trabajo con las llaves como lo son: buscar, añadir y actualizar.

Para evitar una mayor pérdida de datos, cada nodo chord guarda las llaves de su predecesor para que en caso de que este se desconecte integrarlas a su diccionario. Cuando un nodo falla no debemos permitir que esto interrumpa las consultas que se encuentran en proceso mientras el sistema se está reestabilizando. Esto se logra teniendo actualizados los punteros de sucesores y manteniendo en cada nodo chord una lista con sus sucesores más cercanos en el anillo; por tanto, si un nodo nota que su sucesor ha fallado lo reemplaza con la primera entrada activa en la lista de sucesores. 

#### ¿Cómo ejecutar el código?

Para verificar que el funcionamiento del proyecto en red es correcto se utilizó la herramienta Docker, a continuación se explican los pasos a seguir. 

Lo primero es ejecutar los siguientes comandos en la carpeta del proyecto: 

```
docker build -t image/scrapper .
docker network create --subnet 10.0.0.0/20 scrapper-net
docker-compose up
```

Luego abrir una consola por cada nodo que vaya a pertenecer al sistema y ejecutar el siguiente comando: 

```
docker exec -it <name> bash
```

donde \<name\> es uno de los nombres disponibles en el archivo docker-compose.yml.

Una vez se tienen todas las consolas disponibles, se procede a iniciar los nodos. El primer paso es iniciar el name server de Pyro utilizando el siguiente comando:

```bash
pyro4-ns -n <host_name>   
```

donde <host_name> es el ip correspondiente.

El primer nodo chord que se una al sistema debe ejecutar el siguiente comando, donde \<m> es la cantidad de bits e \<ip:port> corresponde a su ip y puerto:

```
python3 chord.py <ip:port> <m>
```

Los nodos de tipo chord restantes deben introducir además como segundo parámetro el ip y el puerto del nodo al que le va a hacer la petición de join:

```
python3 chord.py <ip:port> <ip_chord:port_chord> <m>
```

Para iniciar el primer nodo scrapper debe ejecutar: 

```
python3 scrapper.py <ip:port> <ip_chord:port_chord> <m>
```

donde \<ip:chord> corresponde a su ip y puerto, <ip_chord : port_chord> corresponde a un ip y un puerto de un nodo chord que conozca y \<m> es la cantidad de bits:

Si un segundo nodo de tipo scrapper desea unirse al sistema, entonces al comando anterior le agregará el ip y puerto de un nodo scrapper ya existente:

```bash
python3 scrapper.py <ip:port> <ip_scrapper:port_scrapper> <ip_chord:port_chord> <m>
```

El cliente deberá ejecutar el siguiente comando e introducir la url de manera manual en consola:

```
python3 client.py <ip_scrapp:port_scrapp>
```

Dentro de la carpeta donde se ejecute el proyecto se tendrán carpetas llamadas 'url' seguido de un número: dicho número hace referencia a la cantidad de urls que ha introducido el cliente. Ejemplo si el cliente por primera vez introduce 'http://evea.uh.cu 1' se creará una carpeta 'url0' en la cual se guardará los html http://evea.uh.cu con profundidad 1 y si luego introduce otra url, esta se guardará en la carpeta 'url1'. 

#### Caso de prueba:

1- Iniciar el name server de Pyro:

```
pyro4-ns -n 10.0.0.11
```

2- Iniciar tres nodos chord:

```
python chord.py 10.0.0.2:8000 4
python chord.py 10.0.0.3:8000 10.0.0.2:8000 4
python chord.py 10.0.0.4:8000 10.0.0.3:8000 4
```

Se imprime la informacion de cada nodo:

```
Node 0
Predecessor: 10
Successor: 7
Finger table:
Start 1   Node 7
Start 2   Node 7
Start 4   Node 7
Start 8   Node 10
Keys:

Node 7
Predecessor: 0
Successor: 10
Finger table:
Start 8   Node 10
Start 9   Node 10
Start 11   Node 0
Start 15   Node 0
Keys:

Node 10
Predecessor: 7
Successor: 0
Finger table:
Start 11   Node 0
Start 12   Node 0
Start 14   Node 0
Start 2   Node 7
Keys:
```

3- Al desconectar el nodo 7, las finger tables quedan:

```
Node 0
Predecessor: 10
Successor: 10
Finger table:
Start 1   Node 10
Start 2   Node 10
Start 4   Node 10
Start 8   Node 10
Keys:

Node 10
Predecessor: 0
Successor: 0
Finger table:
Start 11   Node 0
Start 12   Node 0
Start 14   Node 0
Start 2   Node 10
Keys:
```

4- Reconectar el nodo 7:

```
python chord.py 10.0.0.3:8000 10.0.0.2:8000 4
```

5- Iniciar dos nodos scrapper:

```
python scrapper.py 10.0.0.7:8000 10.0.0.2:8000 4
python scrapper.py 10.0.0.8:8000 10.0.0.7:8000 10.0.0.2:8000 4
```

Se imprime la información de cada uno:

```
Address: 10.0.0.7:8000
Chord node: 0
Chord node successors list: [7, 10]
Scrappers list: ['10.0.0.7:8000', '10.0.0.8:8000']

Address: 10.0.0.8:8000
Chord node: 0
Chord node successors list: [7, 10]
Scrappers list: ['10.0.0.8:8000', '10.0.0.7:8000']
```

6- Iniciar dos clientes, los cuales le van a hacer las consultas al nodo scrapper con dirección 10.0.0.7:8000, ejecutando en dos consolas diferentes el siguiente comando:

```
python client.py 10.0.0.7:8000
```

7- En cada cliente introducir una url diferente con una profundidad, y mientras lo hace desconectar el nodo chord 0, para comprobar que las consultas se siguen realizando. Ejemplo de dos url serían:

```
http://evea.uh.cu 1
http://www.cubaeduca.cu 1
```

Luego de esto los nodos chord quedan de la siguiente forma:

```
Node 7
Predecessor: 10
Successor: 10
Finger table:
Start 8   Node 10
Start 9   Node 10
Start 11   Node 7
Start 15   Node 7
Keys:
6 http://evea.uh.cu
1 https://evea.uh.cu/login/index.php?lang=it
1 https://evea.uh.cu/login/index.php?lang=ru
7 https://evea.uh.cu/login/index.php?lang=ja_wp
14 https://evea.uh.cu/login/index.php?lang=en
14 https://evea.uh.cu/login/index.php?lang=es_mx
14 https://evea.uh.cu/login/index.php?lang=fr
12 https://evea.uh.cu/login/index.php?lang=pt
4 https://evea.uh.cu/login/forgot_password.php
13 https://evea.uh.cu/admin/tool/dataprivacy/summary.php

Node 10
Predecessor: 7
Successor: 7
Finger table:
Start 11   Node 7
Start 12   Node 7
Start 14   Node 7
Start 2   Node 7
Keys:
8 https://evea.uh.cu/login/index.php?lang=de
9 http://www.cubaeduca.cu
10 https://evea.uh.cu/login/index.php?lang=ja
10 https://evea.uh.cu/login/index.php?lang=zh_tw
```

Y los nodos scrapper:

```
Address: 10.0.0.7:8000
Chord node: 7
Chord node successors list: [10, 0]
Scrappers list: ['10.0.0.7:8000', '10.0.0.8:8000']

Address: 10.0.0.8:8000
Chord node: 7
Chord node successors list: [10, 0]
Scrappers list: ['10.0.0.8:8000', '10.0.0.7:8000']
```

