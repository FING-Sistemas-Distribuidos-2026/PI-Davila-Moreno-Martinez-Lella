package com.wandanara.backend_api.listener;

import com.wandanara.backend_api.config.RabbitConfig;
import com.wandanara.backend_api.entity.SearchResult;
import com.wandanara.backend_api.message.ProductResult;
import com.wandanara.backend_api.message.ScrapingResultMessage;
import com.wandanara.backend_api.repository.SearchResultRepository;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Component;

@Component
public class ScrapingResultListener {

    private final SimpMessagingTemplate messagingTemplate;
    private final SearchResultRepository searchResultRepository;
    private final com.wandanara.backend_api.repository.SearchRepository searchRepository;

    public ScrapingResultListener(SimpMessagingTemplate messagingTemplate,
                                  SearchResultRepository searchResultRepository,
                                  com.wandanara.backend_api.repository.SearchRepository searchRepository) {
        this.messagingTemplate = messagingTemplate;
        this.searchResultRepository = searchResultRepository;
        this.searchRepository = searchRepository;
    }

    @RabbitListener(queues = RabbitConfig.RESULTS_QUEUE)
    public void handleScrapingResult(ScrapingResultMessage message) {

        System.out.println("====================================");
        System.out.println("Resultado recibido desde RabbitMQ");
        System.out.println("Search ID: " + message.getSearchId());
        System.out.println("Store: " + message.getStore());
        System.out.println("Status: " + message.getStatus());

        if (message.getResults() != null) {
            for (ProductResult product : message.getResults()) {

                SearchResult searchResult = new SearchResult(
                        message.getSearchId(),
                        message.getStore(),
                        product.getName(),
                        product.getPrice(),
                        product.getUrl()
                );

                searchResultRepository.save(searchResult);

                System.out.println("- " + product.getName()
                        + " | $" + product.getPrice()
                        + " | " + product.getUrl());
            }
        }

        String destination = "/topic/search/" + message.getSearchId();

        messagingTemplate.convertAndSend(destination, message);

        com.wandanara.backend_api.entity.Search search = searchRepository.findById(message.getSearchId()).orElse(null);
        if (search != null && "PROCESSING".equals(search.getStatus())) {
            search.setStatus("COMPLETED");
            searchRepository.save(search);
        }

        System.out.println("Resultado guardado en DB y enviado por WebSocket a: " + destination);
        System.out.println("====================================");
    }
}