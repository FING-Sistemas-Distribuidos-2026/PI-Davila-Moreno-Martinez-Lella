package com.wandanara.backend_api.controller;

import com.wandanara.backend_api.config.RabbitConfig;
import com.wandanara.backend_api.entity.Search;
import com.wandanara.backend_api.entity.SearchResult;
import com.wandanara.backend_api.message.ProductResult;
import com.wandanara.backend_api.message.ScrapingJobMessage;
import com.wandanara.backend_api.message.ScrapingResultMessage;
import com.wandanara.backend_api.repository.SearchRepository;
import com.wandanara.backend_api.repository.SearchResultRepository;

import org.springframework.amqp.rabbit.core.RabbitTemplate;
import org.springframework.http.ResponseEntity;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.stream.Collectors;

@RestController
@RequestMapping("/api/search")
@CrossOrigin(origins = "*")
public class SearchController {

    private final RabbitTemplate rabbitTemplate;
    private final SearchRepository searchRepository;
    private final SearchResultRepository searchResultRepository;
    private final SimpMessagingTemplate messagingTemplate;

    public SearchController(RabbitTemplate rabbitTemplate,
                            SearchRepository searchRepository,
                            SearchResultRepository searchResultRepository,
                            SimpMessagingTemplate messagingTemplate) {
        this.rabbitTemplate = rabbitTemplate;
        this.searchRepository = searchRepository;
        this.searchResultRepository = searchResultRepository;
        this.messagingTemplate = messagingTemplate;
    }

    @PostMapping
    public ResponseEntity<Map<String, String>> createSearch(@RequestBody Map<String, Object> body) {
        String query = (String) body.get("query");

        if (query == null || query.isBlank()) {
            return ResponseEntity.badRequest().body(
                    Map.of("error", "La consulta no puede estar vacía")
            );
        }

        String searchId = (String) body.get("searchId");
        if (searchId == null || searchId.isBlank()) {
            searchId = UUID.randomUUID().toString();
        }

        Search latestSearch = null;
        boolean forceUpdate = body.containsKey("forceUpdate") && (Boolean) body.get("forceUpdate");

        if (!forceUpdate) {
            latestSearch = searchRepository.findFirstByQueryOrderByCreatedAtDesc(query);
        }

        boolean requiresScraping = false;

        List<String> stores;
        Object storesObj = body.get("stores");
        if (storesObj instanceof List) {
            stores = (List<String>) storesObj;
        } else {
            stores = List.of("compragamer", "maximus", "gamingcity");
        }

        if (!forceUpdate && latestSearch != null) {
            List<SearchResult> cachedResults = searchResultRepository.findBySearchId(latestSearch.getId());
            
            Map<String, List<SearchResult>> resultsByStore = cachedResults.stream()
                    .collect(Collectors.groupingBy(SearchResult::getStore));
                    
            for (String store : stores) {
                if (resultsByStore.containsKey(store) && !resultsByStore.get(store).isEmpty()) {
                    // Save cached results under the new searchId so they are persistent for this search
                    List<SearchResult> newSearchResults = new ArrayList<>();
                    List<ProductResult> productResults = new ArrayList<>();
                    
                    for (SearchResult r : resultsByStore.get(store)) {
                        java.time.LocalDateTime actualScrapedAt = r.getScrapedAt();
                        if (actualScrapedAt == null) {
                            actualScrapedAt = latestSearch.getCreatedAt();
                        }
                        SearchResult newResult = new SearchResult(searchId, store, r.getName(), r.getPrice(), r.getUrl(), actualScrapedAt);
                        newSearchResults.add(newResult);
                        productResults.add(new ProductResult(r.getName(), r.getPrice(), r.getUrl()));
                    }
                    searchResultRepository.saveAll(newSearchResults);
                            
                    ScrapingResultMessage resultMsg = new ScrapingResultMessage(
                            searchId, store, "SUCCESS", productResults
                    );
                    
                    System.out.println("DEBUG: is newSearchResults empty? " + newSearchResults.isEmpty());
                    if (!newSearchResults.isEmpty()) {
                        System.out.println("DEBUG: getScrapedAt = " + newSearchResults.get(0).getScrapedAt());
                    }

                    if (!newSearchResults.isEmpty() && newSearchResults.get(0).getScrapedAt() != null) {
                        String tzStr = newSearchResults.get(0).getScrapedAt().atZone(java.time.ZoneId.systemDefault()).toInstant().toString();
                        System.out.println("DEBUG: Setting cachedAt (scraped) to " + tzStr);
                        resultMsg.setCachedAt(tzStr);
                    } else {
                        String tzStr = latestSearch.getCreatedAt().atZone(java.time.ZoneId.systemDefault()).toInstant().toString();
                        System.out.println("DEBUG: Setting cachedAt (fallback) to " + tzStr);
                        resultMsg.setCachedAt(tzStr);
                    }
                    
                    String destination = "/topic/search/" + searchId;
                    messagingTemplate.convertAndSend(destination, resultMsg);
                    System.out.println("Resultados cacheados copiados y enviados para: " + store);
                } else {
                    requiresScraping = true;
                    triggerScrape(searchId, query, store);
                }
            }
        } else {
            requiresScraping = true;
            for (String store : stores) {
                triggerScrape(searchId, query, store);
            }
        }

        Search search = new Search(
                searchId,
                query,
                requiresScraping ? "PROCESSING" : "COMPLETED",
                LocalDateTime.now()
        );
        searchRepository.save(search);
        return ResponseEntity.status(201).body(
                Map.of(
                        "searchId", searchId,
                        "status", "PROCESSING"
                )
        );
    }

    private void triggerScrape(String searchId, String query, String store) {
        ScrapingJobMessage message = new ScrapingJobMessage(searchId, query, store, 0);
        rabbitTemplate.convertAndSend(RabbitConfig.SCRAPING_QUEUE, message);
        System.out.println("Mensaje enviado a RabbitMQ: " + store);
    }

    @GetMapping("/history")
    public ResponseEntity<List<Search>> getHistory() {
        return ResponseEntity.ok(searchRepository.findTop50ByOrderByCreatedAtDesc());
    }

    @GetMapping("/{searchId}/results")
    public ResponseEntity<java.util.Map<String, List<SearchResult>>> getResults(@PathVariable String searchId) {
        if (!searchRepository.existsById(searchId)) {
            return ResponseEntity.notFound().build();
        }

        List<SearchResult> results = searchResultRepository.findBySearchId(searchId);
        
        java.util.Map<String, List<SearchResult>> grouped = results.stream()
                .collect(Collectors.groupingBy(SearchResult::getStore));

        return ResponseEntity.ok(grouped);
    }
}