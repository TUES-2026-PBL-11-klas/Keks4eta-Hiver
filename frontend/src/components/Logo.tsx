import logo from '../assets/logo.svg';

type Props = { size?: number };

export default function Logo({ size = 100 }: Props) {
  return <img src={logo} alt="Hiver logo" width={size} height={size} />;
}