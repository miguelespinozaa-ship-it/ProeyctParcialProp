package com.proyecto.ms2.model;

import org.springframework.data.mongodb.core.mapping.Field;

public class Plato {
    // Sin @Field("id") explícito, Spring Data Mongo trata cualquier propiedad "id" como
    // identificador implícito y la guarda/lee como "_id" — rompe el campo "id" documentado
    // en objetos embebidos (ver MS2-catalogo-restaurantes.md).
    @Field("id")
    private String id;
    private String nombre;
    private String descripcion;
    private double precio;
    private String categoria;
    private boolean disponible;

    public String getId() { return id; }
    public void setId(String id) { this.id = id; }
    public String getNombre() { return nombre; }
    public void setNombre(String nombre) { this.nombre = nombre; }
    public String getDescripcion() { return descripcion; }
    public void setDescripcion(String descripcion) { this.descripcion = descripcion; }
    public double getPrecio() { return precio; }
    public void setPrecio(double precio) { this.precio = precio; }
    public String getCategoria() { return categoria; }
    public void setCategoria(String categoria) { this.categoria = categoria; }
    public boolean isDisponible() { return disponible; }
    public void setDisponible(boolean disponible) { this.disponible = disponible; }
}
