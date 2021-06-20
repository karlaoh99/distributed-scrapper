# DistributedScrapper

En la implementación del proyecto se hace uso de la librería de Python Pyro4, la cual permite de una forma sencilla acceder desde un nodo a los métodos y propiedades de otro nodo que se encuentra en la red. Para acceder a dichos nodos, se necesita conocer su 'uri' pero esto resulta engorroso, por tanto se utilizó un servidor de nombres que permitió asignarle un identificador a cada nodo a partir de su ip y su puerto y con este crear su proxy.

El proyecto esta conformado por tres tipos de nodos diferentes: chord, scrapper y client. El flujo del sistema se comporta de la siguiente forma: Un cliente quiere obtener el html de una url y/o de las url que se encuentran dentro del mismo con una profundidad dada. El cliente le envia esta url a un nodo scrapper del cual conoce su ip y su puerto, este al recibirla la hashea y se la envia a un nodo chord del cual conoce su ip y su puerto. Si este nodo chord logra encontrar esta llave en el sistema entonces retorna su valor, en caso contrario el scrapper obtiene el html de internet y le pide al nodo chord guardarla para futuras consultas. Luego según la profundidad introducida por el cliente, el scrapper repite el mismo procediemiento para obtener todos los html de las url internas; una vez termina se las envía al cliente y este las guarda en diferentes archivos.

Los nodos chord se van a encargar de tener almacenado el html de las url que el cliente consulte al sistema, simulando el comportamiento de una chaché. Se implementaron las funcionalidades descritas en el documento ¨Chord: A Scalable Peer-to-peer Lookup Service for Internet Applications¨ presente en la bibliografia. Entre dichas funcionalidades se encuentra: unir un nodo a la red, actualizar su información, que los mismos puedan abandonar la red sin que el sistema colapse, además de las funciones encargadas del trabajo con las llaves como lo son: buscar, añadir y actualizar.

Para evitar una mayor pérdida de datos, cada nodo chord guarda las llaves de su predecesor para que en caso de que este se desconecte integrarlas a su diccionario. Cuando un nodo falla no debemos permitir que esto interrumpa las consulas que se encuentran en proceso mientras el sistema se está reestabilizando. Esto se logra teniendo actualizados los punteros de sucesores y manteniendo en cada nodo chord una lista con sus sucesores más cercanos en el anillo; por tanto, si un nodo nota que su sucesor ha fallado lo reemplaza con la primera entrada activa en la lista de sucesores. El nodo scrapper también guarda la lista de sucesores del nodo chord que conoce, para que en caso de que este se caiga poder seguir realizando consultas al sistema.

#### ¿Cómo ejecutar el código?

Para verificar que el funcionamiento del proyecto en red es correcto se utilizó la herramienta Docker, a continuación se explican los pasos a seguir. 

Lo primero es ejecutar los siguientes comandos en la carpeta del proyecto: 

```
docker build -t image/scrapper .
docker network create --subnet 10.0.0.0/10 scrapper-net
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

```
python3 scrapper.py <ip:port> <ip_scrapper:port_scrapper> <ip_chord:port_chord> <m>
```

