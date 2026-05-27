package com.wandanara.backend_api.controller;

import com.wandanara.backend_api.config.RabbitConfig;
import com.wandanara.backend_api.entity.Search;
import com.wandanara.backend_api.message.ScrapingJobMessage;
import com.wandanara.backend_api.repository.SearchRepository;
import com.wandanara.backend_api.repository.SearchResultRepository;

import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import com.wandanara.backend_api.entity.SearchResult;
import com.wandanara.backend_api.repository.SearchResultRepository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.UUID;

@RestController
@RequestMapping("/api/search")
@CrossOrigin(origins = "*")
public class SearchController {

    private final RabbitTemplate rabbitTemplate;
    private final SearchRepository searchRepository;
    private final SearchResultRepository searchResultRepository;

    public SearchController(RabbitTemplate rabbitTemplate,
                            SearchRepository searchRepository,
                            SearchResultRepository searchResultRepository) {
        this.rabbitTemplate = rabbitTemplate;
        this.searchRepository = searchRepository;
        this.searchResultRepository = searchResultRepository;
    }

    @PostMapping
    public ResponseEntity<Map<String, String>> createSearch(@RequestBody Map<String, String> body) {
        String query = body.get("query");

        if (query == null || query.isBlank()) {
            return ResponseEntity.badRequest().body(
                    Map.of("error", "La consulta no puede estar vacía")
            );
        }

        String searchId = UUID.randomUUID().toString();

        Search search = new Search(
                searchId,
                query,
                "PROCESSING",
                LocalDateTime.now()
        );

        searchRepository.save(search);

        List<String> stores = List.of("tienda-a", "tienda-b", "tienda-c");

        for (String store : stores) {
            ScrapingJobMessage message = new ScrapingJobMessage(
                    searchId,
                    query,
                    store,
                    0
            );

            rabbitTemplate.convertAndSend(
                    RabbitConfig.SCRAPING_QUEUE,
                    message
            );

            System.out.println("Mensaje enviado a RabbitMQ: " + store);
        }

        return ResponseEntity.status(201).body(
                Map.of(
                        "searchId", searchId,
                        "status", "PROCESSING"
                )
        );
    }

    @GetMapping("/{searchId}/results")
    public ResponseEntity<List<SearchResult>> getResults(@PathVariable String searchId) {
        if (!searchRepository.existsById(searchId)) {
            return ResponseEntity.notFound().build();
        }

        List<SearchResult> results = searchResultRepository.findBySearchId(searchId);

        return ResponseEntity.ok(results);
    }

}