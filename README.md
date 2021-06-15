# DistributedScrapper

#### ¿Cómo ejecutar el código?

Para el ejecutar el código, primeramente es necesario abrir una terminal y ejecutar el siguiente comando que se encarga de iniciar el name server de Pyro:

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