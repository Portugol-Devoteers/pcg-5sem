import axios from "axios";
import { useEffect, useState } from "react";

export const App = () => {
    const [message, setMessage] = useState<string>("");

    useEffect(() => {
        axios.get("http://localhost:8080").then((response) => {
            setMessage(response.data.message);
        });
    }, []);

    return <h1>{message}</h1>;
};
