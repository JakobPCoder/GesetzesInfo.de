import React, { useState, useEffect } from 'react';
import './ListItem.css';
import { Button } from '../Button/Button';

const BACKEND_PORT = process.env.BACKEND_PORT || 8000;
const API_DOMAIN = process.env.API_DOMAIN || "localhost";

function ListItem({ id, title, text, score, query_id, show_id }) {
    const [isExpanded, setIsExpanded] = useState(false);
    const [itemData, setItemData] = useState({
        id,
        title,
        text,
        score,
        query_id,
        show_id,
      });


    useEffect(() => {
    setItemData({
        id,
        title,
        text,
        score,
        query_id,
        show_id,
    });
    }, [id, title, text, score, query_id, show_id]);

    /**
     * Toggles the expanded state of the list item.
     * @function
     */
    const toggleExpand = () => {
        setIsExpanded(!isExpanded);
    };


    /**
     * Handles a rating click on the item.
     * @param {boolean} value The value of the rating (true for positive, false for negative)
     * @async
     */
    const handleRatingClick = (value) => {
       const query = `http://${API_DOMAIN}:${BACKEND_PORT}/api/rate/?id=${encodeURIComponent(itemData.id)}&qid=${encodeURIComponent(itemData.query_id)}&r=${encodeURIComponent(value)}`;

        fetch(query)
            .then((response) => {
                if (!response.ok) {
                    throw new Error(`Network response was not ok: ${response.status}`);
                }
                return response.json();
            })
            .then((data) => {
                if (data.error) {
                    throw new Error(data.error);
                } else if (data.success) {
                    console.log('Item rated successfully');
                } else {
                    throw new Error('Unknown response from server');
                }
            })
            .catch((error) => {
                console.error('Error rating item:', error);
                alert('Error rating item: ' + error.message);
            });
    };

    const handleContentClick = (event) => {
        // Check if the click is not on the interaction bar
        if (!event.target.closest('.list-item-interaction-bar')) {
            toggleExpand();
        }
    };
    
    function InteractionBar() {
        return (
            <div className="list-item-interaction-bar">
            <Button text="This was helpful" baseColor="var(--color-rating-positive)" onClick={() => handleRatingClick("positive")} />
            <Button text="Unrelated" baseColor="var(--color-rating-negative)" onClick={() => handleRatingClick("negative")} />
            </div>
        );
    }
        

    return (
        <div className={`list-item ${isExpanded ? 'expanded' : ''}`} onClick={handleContentClick}>
            <div className="list-item-header">
                <div className="list-item-id">{itemData.show_id}</div>
                <div className="list-item-title">{itemData.title}</div>
                <div className="list-item-score">{itemData.score ? score.toFixed(4) : '0.00'}</div>
                <div className="triangle"></div>
            </div>
            <div className="list-item-content">
                <div className="list-item-content-text">{text}</div>
                <InteractionBar />
            </div>
        </div>
    );
}

export default ListItem;
