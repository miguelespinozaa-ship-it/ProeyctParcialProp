package com.proyecto.ms2.repository;

import java.util.List;

import org.springframework.data.mongodb.repository.MongoRepository;

import com.proyecto.ms2.model.Restaurante;

public interface RestauranteRepository extends MongoRepository<Restaurante, String> {
    List<Restaurante> findByCategoria(String categoria);
    List<Restaurante> findByCiudad(String ciudad);
}
