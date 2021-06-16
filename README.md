# DistributedScrapper

En la implementacion del proyecto se hace uso de la librería de Python Pyro4, la cual permite de una forma sencilla acceder desde un nodo a los métodos y propiedades de otro nodo que se encuentra en la red. Para acceder a dichos nodos, se necesita conocer su uri pero esto resulta engorroso, por tanto se utilizó un servidor de nombres que permitió asignarle un identificador a cada nodo a partir de su ip y su puerto y con este crear su proxy.

El proyecto esta conformado por tres tipos de nodos diferentes: chord, scrapper y client. El flujo del sistema se comporta de la siguiente forma: Un cliente quiere obtener el html de una url y/o de las url que se encuentran dentro del mismo con una profundidad dada. El cliente le envia esta url a un nodo scrapper del cual conoce su ip y su puerto, este al recibirla la hashea y se la envia a un nodo chord del cual conoce su ip y su puerto. Si este nodo chord logra encontrar esta llave en el sistema entonces retorna su valor, en caso contrario el scrapper obtiene el html de internet y le pide al nodo chord guardarla para futuras consultas. Luego según la profundidad introducida por el cliente, el scrapper repite el mismo procediemiento para obtener todos los html de las url internas; una vez termina se las envía al cliente y este las guarda en diferentes archivos.

Los nodos chord se van a encargar de tener almacenado el html de las url que el cliente consulte al sistema, simulando el comportamiento de una chaché. Se implementaron las funcionalidades descritas en el documento ¨Chord: A Scalable Peer-to-peer Lookup Service for Internet Applications¨ presente en la bibliografia. Entre dichas funcionalidades se encuentra: unir un nodo a la red, actualizar su información, que los mismos puedan abandonar la red sin que el sistema colapse, además de las funciones encargadas del trabajo con las llaves como lo son: buscar, añadir y actualizar.

Para evitar una mayor pérdida de datos, cada nodo chord guarda las llaves de su predecesor para que en caso de que este se desconecte integrarlas a su diccionario. Cuando un nodo falla no debemos permitir que esto interrumpa las consulas que se encuentran en proceso mientras el sistema se está reestabilizando. Esto se logra teniendo actualizados los punteros de sucesores y manteniendo en cada nodo chord una lista con sus sucesores más cercanos en el anillo; por tanto, si un nodo nota que su sucesor ha fallado lo reemplaza con la primera entrada activa en la lista de sucesores. 

#### ¿Cómo ejecutar el código?

Para verificar que el funcionamiento del proyecto en red era correcto se utilizó Docker.

Ejecute los siguientes comandos en la carpeta del proyecto: 
```
docker build -t image/chord .
docker network create --subnet 12.0.0.0/24 chord-net
docker-compose up
```

Luego en cada consola que simulará un nodo ejecute el siguiente comando, escoja un número del 1 al 8:
```
docker exec -it chord-node-{1-8} bash
```
Luego en cada consola en donde se escribio el comando anterior ejecute:

El siguiente comando que se encarga de iniciar el name server de Pyro:

```bash
pyro4-ns -n <host_name>   
```

El primer nodo que se una al sistema, debe abrir una consola en la carpeta donde se encuentre el archivo 'chord_node.py' y ejecutar el siguiente comando:

```
python3 chord.py <ip:port> <m>
```

Los nodos restantes deben introducir además el ip y el puerto del nodo al que le van a hacer la petición de join:

```
python3 chord.py <ip:port> <ip:port> <m>
```
Estos dos últimos comandos van a imprimir cada cierto tiempo la información del nodo: id, finger table, keys, ...

Para ejecutar el scrapper debe abrir una consola en la carpeta donde se encuentre el archivo 'scrapper.py' y ejecutar:

```
python3 scrapper.py <ip:port> <ip_chord:port_chord> <m>
```

En donde el ip:port son el puerto e ip del nodo scrappper y el ip_chord, port_chord son el ip y puerto del nodo chord al cual se conectará el nodo scrapper.