
import React, { useState, useEffect } from 'react';
import './sMainPage.css';
import ItemList from './components/ItemList/ItemList';
import { AdsMobile } from './components/ads/ads';
import { Button } from './components/Button/Button';


const BACKEND_PORT = process.env.BACKEND_PORT || 8000;
const API_DOMAIN = process.env.API_DOMAIN || "localhost";

export function VerticalLayout({ children }) {
    return (
        <div className="vert-layout">
            {children}
        </div>
    );
}

export function VerticalPad({ children }) {
    return (
        <div className="vert-pad">
            {children}
        </div>
    );
}



export function Header() {
    return <div className="header"/>;
};


export function Title(props) {
    return <div className="title">
        <p>{props.title}</p>
    </div>
};


export function Footer() {
    return <div className="footer" />;
};


export function Slogan(props) {
    return <div className="slogan">
        <p>{props.slogan}</p>
    </div>;
}
export function IntroText(props) {
    return <div className="intro-text">
        <p>{props.text}</p>
    </div>;
}
export function Intro(props) {
    return <div className="intro">
        {IntroText( props)}
    </div>;
}

export function DisclaimerIcon() {
    return <div className="disclaimer-icon">
        
    </div>;
}

export function DisclaimerText(props) {
    return <div className="disclaimer-text">
        <p>{props.text}</p>
    </div>;
}

export function Disclaimer(props) {
    return <div className="disclaimer">
        {DisclaimerIcon()}
        {DisclaimerText(props)}
    </div>;
}

export function SearchHeader(props) {
    return <div className="search-header">
        <p>{props.count}</p>
    </div>;
}


export function TextEntryContainer(props) {
    const { text, setText } = props;
  
    return (
      <div className="text-entry-container">
        <textarea
          className="text-entry"
          value={text}
          onChange={(event) => setText(event.target.value)}
          placeholder="Gib hier deine Frage ein, oder beschreibe deine Situation..."
        />
      </div>
    );
}

/**
 * Search component that handles the search functionality.
 * 
 * @returns {React.JSX.Element} The Search component.
 */
export function Search() {
    // State variables to store the search text, search results, and error.
    const [text, setText] = useState('');
    const [items, setItems] = useState([]); // Renamed from 'content' to 'items'
    const [lawCount, setLawCount] = useState(0);

    const [error, setError] = useState(null); // For handling any errors


    /**
     * Event handler for the search button click event.
     * Fetches the search results from the API and updates the state variables.
     */

    const updateLawCount = async () => {
        try {
            const response = await fetch(`http://${encodeURIComponent(API_DOMAIN)}:${encodeURIComponent(BACKEND_PORT)}/api/laws/count_raw/`);
            if (!response.ok) {
                throw new Error('Failed to fetch law count');
            }
            const data = await response.json();
            setLawCount(data.count);  // Assuming the API returns { count: number }
        } catch (error) {
            console.error('Error fetching law count:', error);
            setError(`${error}`);
        }
    };

    // Fetch the law count when the component mounts
    useEffect(() => {
        updateLawCount();  // Initial load
    }, []);  // Empty dependency array to run only once when component mounts

        
    const handleClick = () => {
        const query = `http://${encodeURIComponent(API_DOMAIN)}:${encodeURIComponent(BACKEND_PORT)}/api/search?q=${encodeURIComponent(text)}`;

        fetch(query)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json();
            })
            .then(data => {
                if (data.error) {
                    throw new Error(data.error);
                }
                if (data && Array.isArray(data.results)) {
                    const validItems = data.results.filter(item => item.id && item.title && item.text && (item.score !== undefined && item.score !== null));
                    if (validItems.length === 0) {
                        throw new Error('No results found');
                    } else {
                        const replaceIds = (items) => items.map((item, idx) => ({ ...item, id: idx + 1 }));
                        setItems(replaceIds(validItems));
                        setError(null);
                    }
                } else {
                    throw new Error('Search response data format is incorrect');
                }
                updateLawCount();  // Update law count after successful search
            })
            .catch(error => {
                console.error('Error:', error);
                setError(`${error}`);
                setItems([]);
            });
    };
    return (
        <div className="search-container">
            <SearchHeader count={lawCount}/>
            <TextEntryContainer text={text} setText={setText} />
            <Button text="Suchen" onClick={handleClick} />
            <ItemList items={items} error={error} query = {text} /> {/* Pass the items to ItemList */}
        </div>
    );
}

const MainPage = () => {
    return (
        <div className="container">
            <div className="left-placeholder"></div>
            <div className="main-content">
                <Header>
                </Header>
                <VerticalLayout>
                    <VerticalPad>
                        <Title title = "Gesetzesinfo.de" />
                        <Slogan slogan = "Informieren Sie sich über Ihre Rechte!" />
                        <Intro text = 
                            "Sich in den verschiedenen Gesetzesbüchern zurechtzufinden, kann sehr überfordernd sein. 
                            Unser Ziel ist es, Menschen ohne juristische Vorkenntnisse eine Möglichkeit zu bieten, 
                            sich einen übersichtlichen Eindruck über unser Rechtssystem zu verschaffen. 
                            Mit Hilfe unserer Suchfunktion  erhalten Sie relevante Gesetzesauszüge (sowie Definitionen wichtiger juristischer Begriffe), 
                            in dem Sie Ihre Situation schildern. Geben Sie Ihre Frage oder Situation in das Suchfeld ein – je detaillierter Ihre Eingabe, 
                            desto präziser die Antwort. Wir stellen kein offizielle Rechtsberatung dar und übernehmen keine Haftung! 
                            In jedem Fall ist es sinnvoll professionelle Beratung durch einen Anwalt hinzuziehen." />
                        <Disclaimer text = 
                            "Wir stellen ausschließlich Informationen bereit, um Ihnen zu helfen ihre Situation besser zu verstehen und einen besseren Überblick zu erhalten.
                            Wir stellen keine offizielle Rechtsberatung dar und übernehmen keinerlei Haftung! 
                            Die gezeigten Ergebnisse basieren mölicherweise auf mehrere Jahre alten Daten und sind, 
                            auch deswegen, nur als Orientierung zu betrachten." />
                        {/* <AdsMobile /> */}
                        <Search />
                    </VerticalPad>
                </VerticalLayout>
                <Footer>
                </Footer>
            </div>
            <div className="right-placeholder"></div>
        </div>
    );
};

export default MainPage;