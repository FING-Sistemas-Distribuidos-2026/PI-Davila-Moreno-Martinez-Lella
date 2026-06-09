package com.wandanara.backend_api.listener;

import com.wandanara.backend_api.config.RabbitConfig;
import com.wandanara.backend_api.entity.DlqMessage;
import com.wandanara.backend_api.message.ScrapingJobMessage;
import com.wandanara.backend_api.repository.DlqMessageRepository;
import org.springframework.amqp.rabbit.annotation.RabbitListener;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Component;

import java.time.LocalDateTime;

@Component
public class DlqListener {

    private final DlqMessageRepository dlqMessageRepository;
    private final SimpMessagingTemplate messagingTemplate;

    public DlqListener(DlqMessageRepository dlqMessageRepository, SimpMessagingTemplate messagingTemplate) {
        this.dlqMessageRepository = dlqMessageRepository;
        this.messagingTemplate = messagingTemplate;
    }

    @RabbitListener(queues = RabbitConfig.DLQ_QUEUE)
    public void handleDlqMessage(ScrapingJobMessage message) {
        System.out.println("====================================");
        System.out.println("Mensaje recibido en DLQ: " + message.getSearchId() + " para tienda: " + message.getStore());

        DlqMessage dlqMessage = new DlqMessage(
                message.getSearchId(),
                message.getQuery(),
                message.getStore(),
                message.getAttempts(),
                LocalDateTime.now()
        );

        dlqMessage = dlqMessageRepository.save(dlqMessage);

        // Notify frontend in real-time
        messagingTemplate.convertAndSend("/topic/dlq", dlqMessage);

        System.out.println("Mensaje fallido persistido y notificado.");
        System.out.println("====================================");
    }
}
