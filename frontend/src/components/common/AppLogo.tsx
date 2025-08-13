import React from 'react';

type AppLogoProps = {
	variant?: 'wordmark' | 'icon';
	className?: string;
	height?: number;
	showTextFallback?: boolean;
};

/**
 * Displays the recomAMP branding.
 *
 * Place your assets at:
 * - public/branding/recomamp-logo.png (horizontal wordmark)
 * - public/branding/recomamp-icon.png (square icon)
 *
 * The component will fall back to an accessible text brand if the image is missing.
 */
export default function AppLogo({
	variant = 'wordmark',
	className,
	height = 28,
	showTextFallback = true
}: AppLogoProps) {
	const [isBroken, setIsBroken] = React.useState(false);

	if (isBroken && showTextFallback) {
		return (
			<span className={className} style={{ lineHeight: 1 }}>
				recomAMP
			</span>
		);
	}

	const pngSrc = variant === 'icon'
		? '/branding/recomamp-icon.png'
		: '/branding/recomamp-logo.png';

	return (
		<img
			src={pngSrc}
			alt="recomAMP"
			height={height}
			style={{ height, width: 'auto' }}
			className={className}
			onError={() => setIsBroken(true)}
		/>
	);
}


