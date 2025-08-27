import React from 'react';
import { X, Package, DollarSign, Box, Tag, Calendar, ExternalLink } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import asinService, { type ASIN, type ASINDetail } from '../../services/asinService';
import LoadingSpinner from '../LoadingSpinner';

interface ASINDetailModalProps {
  asin: ASIN;
  isOpen: boolean;
  onClose: () => void;
}

const ASINDetailModal: React.FC<ASINDetailModalProps> = ({ asin, isOpen, onClose }) => {
  // Fetch full ASIN details
  const { data: asinDetail, isLoading } = useQuery<ASINDetail>({
    queryKey: ['asin-detail', asin.id],
    queryFn: () => asinService.getASIN(asin.id),
    enabled: isOpen
  });

  if (!isOpen) return null;

  const formatDate = (dateString?: string) => {
    if (!dateString) return 'N/A';
    return new Date(dateString).toLocaleDateString('en-US', {
      year: 'numeric',
      month: 'short',
      day: 'numeric'
    });
  };

  const formatPrice = (price?: number) => {
    if (!price) return 'N/A';
    return `$${price.toFixed(2)}`;
  };

  const formatNumber = (num?: number) => {
    if (num === undefined || num === null) return 'N/A';
    return num.toLocaleString();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-lg shadow-xl max-w-3xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        {/* Header */}
        <div className="flex items-center justify-between p-6 border-b sticky top-0 bg-white">
          <div className="flex items-center">
            <Package className="w-6 h-6 text-blue-600 mr-3" />
            <div>
              <h2 className="text-xl font-semibold">ASIN Details</h2>
              <p className="text-sm text-gray-600">{asin.asin}</p>
            </div>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-500"
          >
            <X className="w-6 h-6" />
          </button>
        </div>

        {/* Content */}
        {isLoading ? (
          <div className="p-12 text-center">
            <LoadingSpinner />
            <p className="mt-4 text-gray-600">Loading details...</p>
          </div>
        ) : asinDetail ? (
          <div className="p-6 space-y-6">
            {/* Basic Information */}
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <Tag className="w-5 h-5 mr-2 text-gray-600" />
                Basic Information
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-gray-600">ASIN</label>
                  <p className="font-mono text-sm">{asinDetail.asin}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Brand</label>
                  <p>{asinDetail.brand || 'N/A'}</p>
                </div>
                <div className="col-span-2">
                  <label className="text-sm text-gray-600">Title</label>
                  <p>{asinDetail.title || 'N/A'}</p>
                </div>
                {asinDetail.description && (
                  <div className="col-span-2">
                    <label className="text-sm text-gray-600">Description</label>
                    <p className="text-sm">{asinDetail.description}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Product Details */}
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <Box className="w-5 h-5 mr-2 text-gray-600" />
                Product Details
              </h3>
              <div className="grid grid-cols-2 gap-4">
                {asinDetail.department && (
                  <div>
                    <label className="text-sm text-gray-600">Department</label>
                    <p>{asinDetail.department}</p>
                  </div>
                )}
                {asinDetail.product_group && (
                  <div>
                    <label className="text-sm text-gray-600">Product Group</label>
                    <p>{asinDetail.product_group}</p>
                  </div>
                )}
                {asinDetail.product_type && (
                  <div>
                    <label className="text-sm text-gray-600">Product Type</label>
                    <p>{asinDetail.product_type}</p>
                  </div>
                )}
                {asinDetail.manufacturer && (
                  <div>
                    <label className="text-sm text-gray-600">Manufacturer</label>
                    <p>{asinDetail.manufacturer}</p>
                  </div>
                )}
                {asinDetail.model && (
                  <div>
                    <label className="text-sm text-gray-600">Model</label>
                    <p>{asinDetail.model}</p>
                  </div>
                )}
                {asinDetail.color && (
                  <div>
                    <label className="text-sm text-gray-600">Color</label>
                    <p>{asinDetail.color}</p>
                  </div>
                )}
                {asinDetail.size && (
                  <div>
                    <label className="text-sm text-gray-600">Size</label>
                    <p>{asinDetail.size}</p>
                  </div>
                )}
                <div>
                  <label className="text-sm text-gray-600">Marketplace</label>
                  <p>{asinDetail.marketplace || 'US'}</p>
                </div>
              </div>
            </div>

            {/* Dimensions */}
            {asinDetail.item_dimensions && (
              <div>
                <h3 className="text-lg font-semibold mb-4 flex items-center">
                  <Box className="w-5 h-5 mr-2 text-gray-600" />
                  Item Dimensions
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  {asinDetail.item_dimensions.length !== undefined && (
                    <div>
                      <label className="text-sm text-gray-600">Length</label>
                      <p>
                        {asinDetail.item_dimensions.length} {asinDetail.item_dimensions.unit_dimension || ''}
                      </p>
                    </div>
                  )}
                  {asinDetail.item_dimensions.width !== undefined && (
                    <div>
                      <label className="text-sm text-gray-600">Width</label>
                      <p>
                        {asinDetail.item_dimensions.width} {asinDetail.item_dimensions.unit_dimension || ''}
                      </p>
                    </div>
                  )}
                  {asinDetail.item_dimensions.height !== undefined && (
                    <div>
                      <label className="text-sm text-gray-600">Height</label>
                      <p>
                        {asinDetail.item_dimensions.height} {asinDetail.item_dimensions.unit_dimension || ''}
                      </p>
                    </div>
                  )}
                  {asinDetail.item_dimensions.weight !== undefined && (
                    <div>
                      <label className="text-sm text-gray-600">Weight</label>
                      <p>
                        {asinDetail.item_dimensions.weight} {asinDetail.item_dimensions.unit_weight || ''}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Sales & Pricing */}
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <DollarSign className="w-5 h-5 mr-2 text-gray-600" />
                Sales & Pricing
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-gray-600">Last Known Price</label>
                  <p className="text-lg font-medium">{formatPrice(asinDetail.last_known_price)}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Est. Monthly Units</label>
                  <p className="text-lg font-medium">{formatNumber(asinDetail.monthly_estimated_units)}</p>
                </div>
                {asinDetail.monthly_estimated_sales !== undefined && (
                  <div>
                    <label className="text-sm text-gray-600">Est. Monthly Sales</label>
                    <p className="text-lg font-medium">{formatPrice(asinDetail.monthly_estimated_sales)}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Relationships */}
            {asinDetail.parent_asin && (
              <div>
                <h3 className="text-lg font-semibold mb-4">Relationships</h3>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="text-sm text-gray-600">Parent ASIN</label>
                    <p className="font-mono text-sm">{asinDetail.parent_asin}</p>
                  </div>
                  {asinDetail.variant_type && (
                    <div>
                      <label className="text-sm text-gray-600">Variant Type</label>
                      <p>{asinDetail.variant_type}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Metadata */}
            <div>
              <h3 className="text-lg font-semibold mb-4 flex items-center">
                <Calendar className="w-5 h-5 mr-2 text-gray-600" />
                Metadata
              </h3>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="text-sm text-gray-600">Status</label>
                  <p>
                    <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium ${
                      asinDetail.active ? 'bg-green-100 text-green-800' : 'bg-gray-100 text-gray-800'
                    }`}>
                      {asinDetail.active ? 'Active' : 'Inactive'}
                    </span>
                  </p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Last Updated</label>
                  <p className="text-sm">{formatDate(asinDetail.updated_at)}</p>
                </div>
                <div>
                  <label className="text-sm text-gray-600">Created</label>
                  <p className="text-sm">{formatDate(asinDetail.created_at)}</p>
                </div>
                {asinDetail.last_imported_at && (
                  <div>
                    <label className="text-sm text-gray-600">Last Imported</label>
                    <p className="text-sm">{formatDate(asinDetail.last_imported_at)}</p>
                  </div>
                )}
              </div>
            </div>

            {/* Amazon Link */}
            <div className="pt-4 border-t">
              <a
                href={`https://www.amazon.com/dp/${asinDetail.asin}`}
                target="_blank"
                rel="noopener noreferrer"
                className="inline-flex items-center text-blue-600 hover:text-blue-700"
              >
                <ExternalLink className="w-4 h-4 mr-2" />
                View on Amazon
              </a>
            </div>
          </div>
        ) : (
          <div className="p-12 text-center">
            <p className="text-gray-600">Failed to load ASIN details</p>
          </div>
        )}
      </div>
    </div>
  );
};

export default ASINDetailModal;