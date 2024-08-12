
import React, { useState } from 'react';
import './sMainPage.css';
import './ItemList.css';
import ItemList from './ItemList';


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
    return <div className="header" />;
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


export function Search() {
    const [text, setText] = useState('');
    const [items, setItems] = useState([]); // Renamed from 'content' to 'items'
    const [error, setError] = useState(null); // For handling any errors

    const handleChange = (event) => {
        setText(event.target.value);
    };

    const handleClick = () => {
        console.log('Button clicked. Fetching data...');

        fetch(`http://localhost:3001/api/search?q=${encodeURIComponent(text)}`)
            .then(response => {
                if (!response.ok) {
                    throw new Error('Network response was not ok');
                }
                return response.json(); // Parse response as JSON
            })
            .then(data => {
                // Validate that the data is an array and contains the right fields
                if (Array.isArray(data)) {
                    const validItems = data.filter(item => 
                        item.id && item.title && item.text
                    );
                    setItems(validItems); // Set the validated items
                    setError(null); // Clear any previous error
                } else {
                    throw new Error('Data format is incorrect');
                }
            })
            .catch(error => {
                console.error('Error fetching data:', error);
                setError('Failed to fetch data. Please try again.');
            });
    };

    return (
        <div className="text-and-fetch-button-container">
            <div className="text-entry-container">
                <textarea
                    className="text-entry"
                    value={text}
                    onChange={handleChange}
                    placeholder="Gib hier deine Frage ein, oder beschreibe deine Situation..."
                />
            </div>

            <div className="button-container">
                <button className="fetch-button" onClick={handleClick}>Fetch Content</button>
            </div>

            {error && <div className="error-message">{error}</div>} {/* Display error if any */}
            <ItemList items={items} /> {/* Pass the items to ItemList */}
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