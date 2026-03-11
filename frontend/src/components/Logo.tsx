interface LogoProps {
  className?: string;
}

export default function Logo({ className = "" }: LogoProps) {
  return (
    <svg className={className} viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
      <circle cx="12" cy="12" r="11" fill="#1a1a2e"/>
      <path d="M12 4V14M12 14L8 10M12 14L16 10" stroke="#1DB954" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
      <path d="M7 17C9 16 11 16 13 17C15 18 17 18 19 17" stroke="#1DB954" strokeWidth="2" strokeLinecap="round" opacity="0.9"/>
      <path d="M5 20C8 18 11 18 13 20C15 22 18 21 21 19" stroke="#1DB954" strokeWidth="2" strokeLinecap="round" opacity="0.6"/>
    </svg>
  );
}