import { Navigate } from 'react-router-dom';
import { getAuth } from '../lib/auth';

const PrivateRoute = ({ children, requiredType }) => {
  const { token, userType } = getAuth();
  
  console.log('🔐 PrivateRoute check:', { 
    hasToken: !!token, 
    userType, 
    requiredType,
    tokenPreview: token?.substring(0, 20) + '...'
  });

  if (!token) {
    console.log('❌ No token found - redirecting to login');
    // Redirecionar para a página de login correta baseado no tipo requerido
    const loginPath = requiredType === 'admin' ? '/admin/login' :
                      requiredType === 'agent' ? '/atendente/login' :
                      requiredType === 'reseller' ? '/revenda/login' :
                      '/';
    return <Navigate to={loginPath} replace />;
  }

  if (requiredType && userType !== requiredType) {
    console.log(`❌ UserType mismatch: "${userType}" !== "${requiredType}"`);
    // Redirecionar para a página de login correta
    const loginPath = requiredType === 'admin' ? '/admin/login' :
                      requiredType === 'agent' ? '/atendente/login' :
                      requiredType === 'reseller' ? '/revenda/login' :
                      '/';
    return <Navigate to={loginPath} replace />;
  }

  console.log('✅ PrivateRoute passed - rendering protected content');
  return children;
};

export default PrivateRoute;
