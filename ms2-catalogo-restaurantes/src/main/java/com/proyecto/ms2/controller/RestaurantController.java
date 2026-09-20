package com.proyecto.ms2.controller;

import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Sort;
import org.springframework.http.HttpStatus;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.server.ResponseStatusException;

import com.proyecto.ms2.model.Restaurante;
import com.proyecto.ms2.repository.RestauranteRepository;
import com.proyecto.ms2.security.AuthenticatedUser;
import com.proyecto.ms2.security.JwtAuthFilter;

import jakarta.servlet.http.HttpServletRequest;

@RestController
@RequestMapping("/api/v1/restaurants")
public class RestaurantController {

    private final RestauranteRepository restauranteRepository;

    public RestaurantController(RestauranteRepository restauranteRepository) {
        this.restauranteRepository = restauranteRepository;
    }

    private static final int DEFAULT_PAGE_SIZE = 20;
    private static final int MAX_PAGE_SIZE = 100;

    /**
     * Sin page/page_size devuelve todo (array, como siempre); con ellos, {items, page, page_size, total, total_pages}.
     * page_size por defecto 20 y máximo 100 (si piden más se limita). Header X-Total-Count en ambos modos.
     */
    @GetMapping
    public ResponseEntity<Object> listar(@RequestParam(required = false) String categoria,
                                          @RequestParam(required = false) String ciudad,
                                          @RequestParam(required = false) Integer page,
                                          @RequestParam(name = "page_size", required = false) Integer pageSize) {
        if (page == null && pageSize == null) {
            List<Restaurante> todos = categoria != null ? restauranteRepository.findByCategoria(categoria)
                    : ciudad != null ? restauranteRepository.findByCiudad(ciudad)
                    : restauranteRepository.findAll();
            return ResponseEntity.ok().header("X-Total-Count", String.valueOf(todos.size())).body(todos);
        }

        int numero = page != null ? page : 1;
        int tamano = pageSize != null ? pageSize : DEFAULT_PAGE_SIZE;
        if (numero < 1 || tamano < 1) {
            throw new ResponseStatusException(HttpStatus.BAD_REQUEST, "page y page_size deben ser enteros >= 1");
        }
        tamano = Math.min(tamano, MAX_PAGE_SIZE);

        PageRequest pedido = PageRequest.of(numero - 1, tamano, Sort.by("id"));
        Page<Restaurante> resultado = categoria != null ? restauranteRepository.findByCategoria(categoria, pedido)
                : ciudad != null ? restauranteRepository.findByCiudad(ciudad, pedido)
                : restauranteRepository.findAll(pedido);

        Map<String, Object> cuerpo = new LinkedHashMap<>();
        cuerpo.put("items", resultado.getContent());
        cuerpo.put("page", numero);
        cuerpo.put("page_size", tamano);
        cuerpo.put("total", resultado.getTotalElements());
        cuerpo.put("total_pages", resultado.getTotalPages());
        return ResponseEntity.ok().header("X-Total-Count", String.valueOf(resultado.getTotalElements())).body(cuerpo);
    }

    @GetMapping("/{restaurantId}")
    public Restaurante detalle(@PathVariable String restaurantId) {
        return findOrThrow(restaurantId);
    }

    @GetMapping("/{restaurantId}/admin")
    public Restaurante adminView(@PathVariable String restaurantId, HttpServletRequest request) {
        requireOwnerAdmin(request, restaurantId);
        return findOrThrow(restaurantId);
    }

    @PutMapping("/{restaurantId}")
    public Restaurante actualizar(@PathVariable String restaurantId, @RequestBody Restaurante datos, HttpServletRequest request) {
        requireOwnerAdmin(request, restaurantId);
        Restaurante existente = findOrThrow(restaurantId);
        existente.setNombre(datos.getNombre());
        existente.setDireccion(datos.getDireccion());
        existente.setCategoria(datos.getCategoria());
        existente.setCiudad(datos.getCiudad());
        return restauranteRepository.save(existente);
    }

    private Restaurante findOrThrow(String restaurantId) {
        return restauranteRepository.findById(restaurantId)
                .orElseThrow(() -> new ResponseStatusException(HttpStatus.NOT_FOUND, "Restaurante no encontrado"));
    }

    /** Compartido con MenuController: exige JWT admin cuyo restaurante_id coincida con la ruta. */
    static void requireOwnerAdmin(HttpServletRequest request, String restaurantId) {
        AuthenticatedUser user = (AuthenticatedUser) request.getAttribute(JwtAuthFilter.REQUEST_ATTR);
        if (user == null) {
            throw new ResponseStatusException(HttpStatus.UNAUTHORIZED, "Falta token de autenticación");
        }
        if (!user.isAdmin() || !restaurantId.equals(user.getRestauranteId())) {
            throw new ResponseStatusException(HttpStatus.FORBIDDEN, "No autorizado para este restaurante");
        }
    }
}
